/*
 * SPDX-License-Identifier: LicenseRef-CSSL-1.0
 */

/*
 * AAL compute extension, AAL Implementation side.
 *
 * The AALI-C-App operations below are served on a UNIX stream socket, one request per line, one JSON object per
 * response line:
 *
 *   getAalLpuComputeCapabilities
 *   setAalLpuComputeConfig [expected_version=<v>] <name>=<value> ...
 *   getAalLpuComputeConfig
 *   getAalLpuComputeStats
 *   setAalAccelConfig limits=<file>
 *
 * setAalAccelConfig stands for the AALI-C-Mgmt path (IMS -> HAM): it loads the infrastructure limits, one
 * "<name> <min> <max>" line per parameter. The effective domain of a parameter is its descriptor domain
 * intersected with its limit; a value in force that falls outside a new limit is clamped to it.
 *
 * A set request is validated as a whole before anything is applied: either every value is applied, in one new
 * configuration version, or none is.
 */

#include "aal_compute_ext.h"
#include "bbdev_oai_sw.h"

#include <errno.h>
#include <inttypes.h>
#include <poll.h>
#include <stdarg.h>
#include <stdatomic.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/un.h>
#include <time.h>
#include <unistd.h>

#include "assertions.h"
#include "common/utils/LOG/log.h"
#include "common/utils/system.h"

#define AAL_EXT_LINE_MAX 1024
#define AAL_EXT_RESPONSE_MAX 16384
#define AAL_EXT_MAX_TOKENS 32
/* period at which the control thread checks for shutdown while waiting on the socket */
#define AAL_EXT_POLL_MS 100

typedef enum {
  AAL_EXT_OK,
  AAL_EXT_BAD_REQUEST,
  AAL_EXT_UNKNOWN_PARAM,
  AAL_EXT_INVALID_TYPE,
  AAL_EXT_OUT_OF_RANGE,
  AAL_EXT_LIMIT_EXCEEDED,
  AAL_EXT_VERSION_CONFLICT,
} aal_ext_status_t;

static const char *const aal_ext_status_str[] = {
    [AAL_EXT_OK] = "OK",
    [AAL_EXT_BAD_REQUEST] = "BAD_REQUEST",
    [AAL_EXT_UNKNOWN_PARAM] = "UNKNOWN_PARAM",
    [AAL_EXT_INVALID_TYPE] = "INVALID_TYPE",
    [AAL_EXT_OUT_OF_RANGE] = "OUT_OF_RANGE",
    [AAL_EXT_LIMIT_EXCEEDED] = "LIMIT_EXCEEDED",
    [AAL_EXT_VERSION_CONFLICT] = "VERSION_CONFLICT",
};

static const char *const aal_ext_type_str[] = {
    [AAL_COMPUTE_TYPE_INT] = "INT",
    [AAL_COMPUTE_TYPE_ENUM] = "ENUM",
    [AAL_COMPUTE_TYPE_BOOL] = "BOOL",
};

static const char *const aal_ext_category_str[] = {
    [AAL_COMPUTE_CATEGORY_PARALLELISM] = "PARALLELISM",
    [AAL_COMPUTE_CATEGORY_BATCHING] = "BATCHING",
    [AAL_COMPUTE_CATEGORY_MEMORY] = "MEMORY",
    [AAL_COMPUTE_CATEGORY_OTHER] = "OTHER",
};

static const char *const aal_ext_scope_str[] = {
    [AAL_COMPUTE_SCOPE_LPU] = "LPU",
    [AAL_COMPUTE_SCOPE_PROFILE_INSTANCE] = "PROFILE_INSTANCE",
    [AAL_COMPUTE_SCOPE_PROFILE_QUEUE] = "PROFILE_QUEUE",
};

typedef struct {
  bool set;
  int32_t min;
  int32_t max;
} aal_ext_limit_t;

/* only the control thread touches this state after aal_compute_ext_init() returns */
static struct {
  const aal_compute_lpu_ops_t *lpu; /* NULL: the LPU publishes no runtime parameters */
  aal_ext_limit_t limits[AAL_COMPUTE_MAX_PARAMS];
  uint32_t descriptor_version;
  int listen_fd;
  char sock_path[sizeof(((struct sockaddr_un *)0)->sun_path)];
  pthread_t thread;
  atomic_bool stop;
} ext = {.listen_fd = -1};

static inline int32_t clamp_i32(int32_t v, int32_t lo, int32_t hi)
{
  return v < lo ? lo : (v > hi ? hi : v);
}

typedef struct {
  char buf[AAL_EXT_RESPONSE_MAX];
  size_t len;
} aal_ext_json_t;

static void json_append(aal_ext_json_t *j, const char *fmt, ...) __attribute__((format(printf, 2, 3)));
static void json_append(aal_ext_json_t *j, const char *fmt, ...)
{
  if (j->len >= sizeof(j->buf))
    return;
  va_list ap;
  va_start(ap, fmt);
  const int n = vsnprintf(j->buf + j->len, sizeof(j->buf) - j->len, fmt, ap);
  va_end(ap);
  j->len = (n < 0 || j->len + n >= sizeof(j->buf)) ? sizeof(j->buf) : j->len + n;
}

static int nb_params(void)
{
  return ext.lpu ? ext.lpu->nb_params : 0;
}

static int find_param(const char *name)
{
  for (int i = 0; i < nb_params(); i++)
    if (strcmp(ext.lpu->params[i].name, name) == 0)
      return i;
  return -1;
}

static void effective_domain(int i, int32_t *min, int32_t *max)
{
  const aal_compute_param_t *p = &ext.lpu->params[i];
  *min = p->min;
  *max = p->max;
  if (ext.limits[i].set) {
    *min = ext.limits[i].min > *min ? ext.limits[i].min : *min;
    *max = ext.limits[i].max < *max ? ext.limits[i].max : *max;
  }
}

static aal_ext_status_t parse_value(const aal_compute_param_t *p, const char *s, int32_t *value)
{
  switch (p->type) {
    case AAL_COMPUTE_TYPE_ENUM:
      for (int k = 0; k < p->nb_enum_values; k++)
        if (strcmp(p->enum_values[k], s) == 0) {
          *value = k;
          return AAL_EXT_OK;
        }
      return AAL_EXT_INVALID_TYPE;
    case AAL_COMPUTE_TYPE_BOOL:
      if (strcmp(s, "true") == 0 || strcmp(s, "1") == 0)
        *value = 1;
      else if (strcmp(s, "false") == 0 || strcmp(s, "0") == 0)
        *value = 0;
      else
        return AAL_EXT_INVALID_TYPE;
      return AAL_EXT_OK;
    case AAL_COMPUTE_TYPE_INT: {
      char *end;
      errno = 0;
      const long v = strtol(s, &end, 10);
      if (errno != 0 || end == s || *end != '\0' || v < INT32_MIN || v > INT32_MAX)
        return AAL_EXT_INVALID_TYPE;
      *value = v;
      return AAL_EXT_OK;
    }
  }
  return AAL_EXT_INVALID_TYPE;
}

static aal_ext_status_t check_value(int i, int32_t value)
{
  const aal_compute_param_t *p = &ext.lpu->params[i];
  if (value < p->min || value > p->max || (p->step > 1 && (value - p->min) % p->step != 0))
    return AAL_EXT_OUT_OF_RANGE;
  int32_t min, max;
  effective_domain(i, &min, &max);
  if (value < min || value > max)
    return AAL_EXT_LIMIT_EXCEEDED;
  return AAL_EXT_OK;
}

static void json_value(aal_ext_json_t *j, int i, int32_t value)
{
  const aal_compute_param_t *p = &ext.lpu->params[i];
  if (p->type == AAL_COMPUTE_TYPE_ENUM)
    json_append(j, "\"%s\"", p->enum_values[value]);
  else if (p->type == AAL_COMPUTE_TYPE_BOOL)
    json_append(j, "%s", value ? "true" : "false");
  else
    json_append(j, "%d", value);
}

/*
 * Validates every name=value token against the current values and, only if all are valid, applies them in one
 * version. On error, *bad_token points to the offending token.
 */
static aal_ext_status_t set_config(char **tokens, int nb_tokens, const char **bad_token, uint32_t *version)
{
  int32_t values[AAL_COMPUTE_MAX_PARAMS];
  uint64_t t_applied_ns;
  const uint32_t current_version = ext.lpu ? ext.lpu->get(values, &t_applied_ns) : 0;
  *version = current_version;
  for (int t = 0; t < nb_tokens; t++) {
    *bad_token = tokens[t];
    char *eq = strchr(tokens[t], '=');
    if (eq == NULL)
      return AAL_EXT_BAD_REQUEST;
    *eq = '\0';
    const char *name = tokens[t];
    const char *s = eq + 1;
    if (strcmp(name, "expected_version") == 0) {
      if (strtoul(s, NULL, 10) != current_version)
        return AAL_EXT_VERSION_CONFLICT;
      continue;
    }
    const int i = find_param(name);
    if (i < 0)
      return AAL_EXT_UNKNOWN_PARAM;
    int32_t v;
    aal_ext_status_t st = parse_value(&ext.lpu->params[i], s, &v);
    if (st == AAL_EXT_OK)
      st = check_value(i, v);
    if (st != AAL_EXT_OK)
      return st;
    values[i] = v;
  }
  *bad_token = NULL;
  if (ext.lpu)
    *version = ext.lpu->apply(values);
  return AAL_EXT_OK;
}

/* Loads "<name> <min> <max>" lines; the limits replace the previous ones only if the whole file is valid. */
static int load_limits(const char *path)
{
  FILE *f = fopen(path, "r");
  if (f == NULL) {
    LOG_E(NR_PHY, "AAL compute extension: cannot open limits file %s: %s\n", path, strerror(errno));
    return -1;
  }
  aal_ext_limit_t limits[AAL_COMPUTE_MAX_PARAMS] = {0};
  char line[AAL_EXT_LINE_MAX];
  int line_nb = 0;
  int ret = 0;
  while (ret == 0 && fgets(line, sizeof(line), f) != NULL) {
    line_nb++;
    char name[AAL_EXT_LINE_MAX];
    long min, max;
    char *hash = strchr(line, '#');
    if (hash != NULL)
      *hash = '\0';
    const int n = sscanf(line, "%1023s %ld %ld", name, &min, &max);
    if (n <= 0)
      continue;
    const int i = find_param(name);
    if (n != 3 || i < 0 || min > max) {
      LOG_E(NR_PHY, "AAL compute extension: %s:%d: invalid limit \"%s\"\n", path, line_nb, name);
      ret = -1;
      break;
    }
    limits[i] = (aal_ext_limit_t){.set = true, .min = min, .max = max};
  }
  fclose(f);
  if (ret == 0)
    memcpy(ext.limits, limits, sizeof(ext.limits));
  return ret;
}

/* Clamps the values in force to the effective domain; returns the number of parameters adjusted. */
static int clamp_to_limits(uint32_t *version, aal_ext_json_t *adjusted)
{
  int32_t values[AAL_COMPUTE_MAX_PARAMS];
  uint64_t t_applied_ns;
  *version = ext.lpu ? ext.lpu->get(values, &t_applied_ns) : 0;
  int nb_adjusted = 0;
  for (int i = 0; i < nb_params(); i++) {
    int32_t min, max;
    effective_domain(i, &min, &max);
    const int32_t v = clamp_i32(values[i], min, max);
    if (v != values[i]) {
      json_append(adjusted, "%s\"%s\"", nb_adjusted ? "," : "", ext.lpu->params[i].name);
      values[i] = v;
      nb_adjusted++;
    }
  }
  if (nb_adjusted > 0)
    *version = ext.lpu->apply(values);
  return nb_adjusted;
}

static void op_get_capabilities(aal_ext_json_t *r)
{
  json_append(r,
              ",\"status\":\"OK\",\"aal_lpu_handle\":\"%s\",\"descriptor_version\":%u,\"params\":[",
              ext.lpu ? ext.lpu->lpu_handle : "",
              ext.descriptor_version);
  for (int i = 0; i < nb_params(); i++) {
    const aal_compute_param_t *p = &ext.lpu->params[i];
    int32_t min, max;
    effective_domain(i, &min, &max);
    json_append(r, "%s{\"name\":\"%s\",\"type\":\"%s\"", i ? "," : "", p->name, aal_ext_type_str[p->type]);
    if (p->type == AAL_COMPUTE_TYPE_ENUM) {
      json_append(r, ",\"values\":[");
      for (int k = min; k <= max; k++)
        json_append(r, "%s\"%s\"", k > min ? "," : "", p->enum_values[k]);
      json_append(r, "]");
    } else if (p->type == AAL_COMPUTE_TYPE_INT) {
      json_append(r, ",\"min\":%d,\"max\":%d,\"step\":%d", min, max, p->step);
    }
    json_append(r, ",\"default\":");
    json_value(r, i, p->default_value);
    if (p->unit != NULL && p->unit[0] != '\0')
      json_append(r, ",\"unit\":\"%s\"", p->unit);
    json_append(r,
                ",\"category\":\"%s\",\"scope\":\"%s\",\"description\":\"%s\"}",
                aal_ext_category_str[p->category],
                aal_ext_scope_str[p->scope],
                p->description);
  }
  json_append(r, "]");
}

static void op_get_config(aal_ext_json_t *r)
{
  int32_t values[AAL_COMPUTE_MAX_PARAMS];
  uint64_t t_applied_ns = 0;
  const uint32_t version = ext.lpu ? ext.lpu->get(values, &t_applied_ns) : 0;
  json_append(r, ",\"status\":\"OK\",\"version\":%u,\"t_applied_ns\":%" PRIu64 ",\"values\":{", version, t_applied_ns);
  for (int i = 0; i < nb_params(); i++) {
    json_append(r, "%s\"%s\":", i ? "," : "", ext.lpu->params[i].name);
    json_value(r, i, values[i]);
  }
  json_append(r, "}");
}

static void op_get_stats(aal_ext_json_t *r)
{
  aal_compute_stats_t stats[AAL_COMPUTE_STATS_VERSIONS];
  const int n = ext.lpu ? ext.lpu->get_stats(stats, AAL_COMPUTE_STATS_VERSIONS) : 0;
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  json_append(r, ",\"status\":\"OK\",\"now_ns\":%" PRIu64 ",\"versions\":[", (uint64_t)(ts.tv_sec * 1000000000LL + ts.tv_nsec));
  for (int k = 0; k < n; k++)
    json_append(r,
                "%s{\"version\":%u,\"t_applied_ns\":%" PRIu64 ",\"t_first_burst_ns\":%" PRIu64 ",\"bursts\":%" PRIu64
                ",\"ops\":%" PRIu64 ",\"busy_ns\":%" PRIu64 "}",
                k ? "," : "",
                stats[k].version,
                stats[k].t_applied_ns,
                stats[k].t_first_burst_ns,
                stats[k].nb_bursts,
                stats[k].nb_ops,
                stats[k].busy_ns);
  json_append(r, "]");
}

static void op_set_config(char **tokens, int nb_tokens, aal_ext_json_t *r)
{
  const char *bad_token;
  uint32_t version;
  const aal_ext_status_t st = set_config(tokens, nb_tokens, &bad_token, &version);
  json_append(r, ",\"status\":\"%s\",\"version\":%u", aal_ext_status_str[st], version);
  if (st != AAL_EXT_OK)
    json_append(r, ",\"param\":\"%s\"", bad_token);
}

static void op_set_accel_config(char **tokens, int nb_tokens, aal_ext_json_t *r)
{
  if (nb_tokens != 1 || strncmp(tokens[0], "limits=", strlen("limits=")) != 0) {
    json_append(r, ",\"status\":\"%s\"", aal_ext_status_str[AAL_EXT_BAD_REQUEST]);
    return;
  }
  if (load_limits(tokens[0] + strlen("limits=")) != 0) {
    json_append(r, ",\"status\":\"%s\"", aal_ext_status_str[AAL_EXT_BAD_REQUEST]);
    return;
  }
  ext.descriptor_version++;
  aal_ext_json_t adjusted = {0};
  uint32_t version;
  clamp_to_limits(&version, &adjusted);
  json_append(r,
              ",\"status\":\"OK\",\"descriptor_version\":%u,\"version\":%u,\"adjusted\":[%s]",
              ext.descriptor_version,
              version,
              adjusted.buf);
}

static void handle_request(char *line, aal_ext_json_t *r)
{
  char *tokens[AAL_EXT_MAX_TOKENS];
  int nb_tokens = 0;
  char *save;
  for (char *t = strtok_r(line, " \t\r", &save); t != NULL && nb_tokens < AAL_EXT_MAX_TOKENS; t = strtok_r(NULL, " \t\r", &save))
    tokens[nb_tokens++] = t;
  if (nb_tokens == 0) {
    json_append(r, "{\"op\":\"\",\"status\":\"%s\"}", aal_ext_status_str[AAL_EXT_BAD_REQUEST]);
    return;
  }
  const char *op = tokens[0];
  json_append(r, "{\"op\":\"%s\"", op);
  if (strcmp(op, "getAalLpuComputeCapabilities") == 0 && nb_tokens == 1)
    op_get_capabilities(r);
  else if (strcmp(op, "setAalLpuComputeConfig") == 0)
    op_set_config(tokens + 1, nb_tokens - 1, r);
  else if (strcmp(op, "getAalLpuComputeConfig") == 0 && nb_tokens == 1)
    op_get_config(r);
  else if (strcmp(op, "getAalLpuComputeStats") == 0 && nb_tokens == 1)
    op_get_stats(r);
  else if (strcmp(op, "setAalAccelConfig") == 0)
    op_set_accel_config(tokens + 1, nb_tokens - 1, r);
  else
    json_append(r, ",\"status\":\"%s\"", aal_ext_status_str[AAL_EXT_BAD_REQUEST]);
  json_append(r, "}\n");
}

/* waits until fd is readable or shutdown is requested; returns false on shutdown */
static bool wait_readable(int fd)
{
  struct pollfd pfd = {.fd = fd, .events = POLLIN};
  while (!atomic_load(&ext.stop)) {
    const int n = poll(&pfd, 1, AAL_EXT_POLL_MS);
    if (n > 0)
      return true;
    if (n < 0 && errno != EINTR)
      return false;
  }
  return false;
}

static void serve_client(int fd)
{
  char line[AAL_EXT_LINE_MAX];
  size_t len = 0;
  while (wait_readable(fd)) {
    const ssize_t n = read(fd, line + len, sizeof(line) - 1 - len);
    if (n <= 0)
      return;
    len += n;
    char *nl;
    while ((nl = memchr(line, '\n', len)) != NULL) {
      *nl = '\0';
      aal_ext_json_t r = {0};
      handle_request(line, &r);
      if (write(fd, r.buf, r.len) != (ssize_t)r.len)
        return;
      len -= nl + 1 - line;
      memmove(line, nl + 1, len);
    }
    if (len == sizeof(line) - 1) {
      LOG_W(NR_PHY, "AAL compute extension: request longer than %d bytes, closing connection\n", AAL_EXT_LINE_MAX - 1);
      return;
    }
  }
}

static void *ctl_thread(void *arg)
{
  while (wait_readable(ext.listen_fd)) {
    const int fd = accept(ext.listen_fd, NULL, NULL);
    if (fd < 0)
      continue;
    serve_client(fd);
    close(fd);
  }
  return NULL;
}

static int start_ctl_socket(const char *path)
{
  struct sockaddr_un addr = {.sun_family = AF_UNIX};
  if (strlen(path) >= sizeof(addr.sun_path)) {
    LOG_E(NR_PHY, "AAL compute extension: socket path too long: %s\n", path);
    return -1;
  }
  strcpy(addr.sun_path, path);
  strcpy(ext.sock_path, path);
  ext.listen_fd = socket(AF_UNIX, SOCK_STREAM, 0);
  if (ext.listen_fd < 0) {
    LOG_E(NR_PHY, "AAL compute extension: socket(): %s\n", strerror(errno));
    return -1;
  }
  unlink(path);
  if (bind(ext.listen_fd, (struct sockaddr *)&addr, sizeof(addr)) != 0 || listen(ext.listen_fd, 1) != 0) {
    LOG_E(NR_PHY, "AAL compute extension: cannot listen on %s: %s\n", path, strerror(errno));
    close(ext.listen_fd);
    ext.listen_fd = -1;
    return -1;
  }
  /* the process runs as root (DPDK); the control client does not need to */
  chmod(path, 0666);
  atomic_store(&ext.stop, false);
  threadCreate(&ext.thread, ctl_thread, NULL, "aal_ext_ctl", -1, OAI_PRIORITY_RT_LOW);
  return 0;
}

static const aal_compute_lpu_ops_t *lpu_ops_for_driver(const char *driver_name)
{
  const aal_compute_lpu_ops_t *oai_sw = oai_sw_compute_ops();
  if (strcmp(driver_name, oai_sw->lpu_handle) == 0)
    return oai_sw;
  return NULL;
}

int aal_compute_ext_init(const char *driver_name, const char *ctl_sock, const char *limits_file, const char *initial_config)
{
  ext.lpu = lpu_ops_for_driver(driver_name);
  ext.descriptor_version = 1;
  if (ext.lpu != NULL)
    AssertFatal(ext.lpu->nb_params <= AAL_COMPUTE_MAX_PARAMS, "%s publishes too many parameters\n", driver_name);

  if (limits_file != NULL && limits_file[0] != '\0') {
    if (load_limits(limits_file) != 0)
      return -1;
    aal_ext_json_t adjusted = {0};
    uint32_t version;
    clamp_to_limits(&version, &adjusted);
  }

  if (initial_config != NULL && initial_config[0] != '\0') {
    char buf[AAL_EXT_LINE_MAX];
    snprintf(buf, sizeof(buf), "%s", initial_config);
    char *tokens[AAL_EXT_MAX_TOKENS];
    int nb_tokens = 0;
    char *save;
    for (char *t = strtok_r(buf, ",", &save); t != NULL && nb_tokens < AAL_EXT_MAX_TOKENS; t = strtok_r(NULL, ",", &save))
      tokens[nb_tokens++] = t;
    const char *bad_token;
    uint32_t version;
    const aal_ext_status_t st = set_config(tokens, nb_tokens, &bad_token, &version);
    if (st != AAL_EXT_OK) {
      LOG_E(NR_PHY, "AAL compute extension: initial configuration rejected: %s (%s)\n", aal_ext_status_str[st], bad_token);
      return -1;
    }
  }

  for (int i = 0; i < nb_params(); i++) {
    int32_t min, max;
    effective_domain(i, &min, &max);
    LOG_I(NR_PHY, "AAL compute extension: %s publishes %s [%d..%d]\n", driver_name, ext.lpu->params[i].name, min, max);
  }
  if (start_ctl_socket(ctl_sock) != 0)
    return -1;
  LOG_I(NR_PHY, "AAL compute extension: AALI-C-App operations on %s\n", ctl_sock);
  return 0;
}

void aal_compute_ext_shutdown(void)
{
  if (ext.listen_fd < 0)
    return;
  atomic_store(&ext.stop, true);
  pthread_join(ext.thread, NULL);
  close(ext.listen_fd);
  unlink(ext.sock_path);
  ext.listen_fd = -1;
}
