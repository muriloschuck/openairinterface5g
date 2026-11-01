/*
 * SPDX-License-Identifier: LicenseRef-CSSL-1.0
 */

/*
 * Unit test of the AAL compute extension (aal_compute_ext.c) against a fake LPU, through the control socket as a
 * client would use it: discovery, validation of every error class, all-or-nothing application, versioning,
 * infrastructure limits (including limits that leave no valid value), JSON escaping of echoed request tokens, and a
 * client that closes early. No DPDK is involved.
 */

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

#include "aal_compute_ext.h"
#include "common/utils/LOG/log.h"

static const aal_compute_param_t fake_params[] = {
    {.name = "t.mode",
     .type = AAL_COMPUTE_TYPE_ENUM,
     .min = 0,
     .max = 1,
     .step = 1,
     .nb_enum_values = 2,
     .enum_values = {"seq", "par"},
     .default_value = 0,
     .category = AAL_COMPUTE_CATEGORY_PARALLELISM,
     .scope = AAL_COMPUTE_SCOPE_LPU,
     .description = "mode"},
    {.name = "t.workers",
     .type = AAL_COMPUTE_TYPE_INT,
     .min = 1,
     .max = 16,
     .step = 1,
     .default_value = 1,
     .unit = "threads",
     .category = AAL_COMPUTE_CATEGORY_PARALLELISM,
     .scope = AAL_COMPUTE_SCOPE_LPU,
     .description = "workers"},
    {.name = "t.batch",
     .type = AAL_COMPUTE_TYPE_INT,
     .min = 2,
     .max = 64,
     .step = 2,
     .default_value = 2,
     .unit = "CBs",
     .category = AAL_COMPUTE_CATEGORY_BATCHING,
     .scope = AAL_COMPUTE_SCOPE_LPU,
     .description = "batch, \"quoted\""},
    {.name = "t.flag",
     .type = AAL_COMPUTE_TYPE_BOOL,
     .min = 0,
     .max = 1,
     .step = 1,
     .default_value = 0,
     .category = AAL_COMPUTE_CATEGORY_OTHER,
     .scope = AAL_COMPUTE_SCOPE_PROFILE_QUEUE,
     .description = "flag"},
};
#define NB_FAKE_PARAMS (int)(sizeof(fake_params) / sizeof(fake_params[0]))

static int32_t fake_values[NB_FAKE_PARAMS] = {0, 1, 2, 0};
static uint32_t fake_version = 1;
static int fake_applies;

static uint32_t fake_apply(const int32_t *values)
{
  memcpy(fake_values, values, sizeof(fake_values));
  fake_applies++;
  return ++fake_version;
}

static uint32_t fake_get(int32_t *values, uint64_t *t_applied_ns)
{
  memcpy(values, fake_values, sizeof(fake_values));
  *t_applied_ns = 0;
  return fake_version;
}

static int fake_get_stats(aal_compute_stats_t *stats, int max)
{
  return 0;
}

static const aal_compute_lpu_ops_t fake_lpu = {
    .lpu_handle = "fake_lpu",
    .nb_params = NB_FAKE_PARAMS,
    .params = fake_params,
    .apply = fake_apply,
    .get = fake_get,
    .get_stats = fake_get_stats,
};

static char sock_path[108];
static int failures;

#define CHECK(cond, ...)                                   \
  do {                                                     \
    if (!(cond)) {                                         \
      failures++;                                          \
      fprintf(stderr, "FAIL %s:%d: ", __FILE__, __LINE__); \
      fprintf(stderr, __VA_ARGS__);                        \
      fprintf(stderr, "\n");                               \
    }                                                      \
  } while (0)

static int connect_ctl(void)
{
  struct sockaddr_un addr = {.sun_family = AF_UNIX};
  strcpy(addr.sun_path, sock_path);
  const int fd = socket(AF_UNIX, SOCK_STREAM, 0);
  if (fd < 0 || connect(fd, (struct sockaddr *)&addr, sizeof(addr)) != 0) {
    perror("connect");
    exit(EXIT_FAILURE);
  }
  return fd;
}

/* sends one request line and returns the response line (static buffer) */
static const char *req(const char *line)
{
  static char resp[16384];
  const int fd = connect_ctl();
  char out[1100];
  const int n = snprintf(out, sizeof(out), "%s\n", line);
  if (write(fd, out, n) != n) {
    perror("write");
    exit(EXIT_FAILURE);
  }
  size_t len = 0;
  while (len < sizeof(resp) - 1) {
    const ssize_t r = read(fd, resp + len, sizeof(resp) - 1 - len);
    if (r <= 0)
      break;
    len += r;
    if (resp[len - 1] == '\n')
      break;
  }
  resp[len] = '\0';
  close(fd);
  return resp;
}

static bool has(const char *resp, const char *s)
{
  return strstr(resp, s) != NULL;
}

static void write_file(const char *path, const char *content)
{
  FILE *f = fopen(path, "w");
  if (f == NULL || fputs(content, f) < 0) {
    perror(path);
    exit(EXIT_FAILURE);
  }
  fclose(f);
}

#define EXPECT(line, ...)                                                       \
  do {                                                                          \
    const char *r_ = req(line);                                                 \
    const char *want_[] = {__VA_ARGS__};                                        \
    for (size_t k_ = 0; k_ < sizeof(want_) / sizeof(want_[0]); k_++)            \
      CHECK(has(r_, want_[k_]), "%s -> %s (expected %s)", line, r_, want_[k_]); \
  } while (0)

int main(void)
{
  logInit();
  char dir[] = "/tmp/aal_ext_test_XXXXXX";
  if (mkdtemp(dir) == NULL) {
    perror("mkdtemp");
    return EXIT_FAILURE;
  }
  snprintf(sock_path, sizeof(sock_path), "%s/ctl.sock", dir);
  char limits[200], cmd[300];
  snprintf(limits, sizeof(limits), "%s/limits.txt", dir);

  CHECK(aal_compute_ext_register(&fake_lpu) == 0, "register");
  CHECK(aal_compute_ext_register(&fake_lpu) == -1, "duplicate register must fail");
  CHECK(aal_compute_ext_init("fake_lpu", sock_path, NULL, NULL) == 0, "init");

  /* discovery */
  EXPECT("getAalLpuComputeCapabilities",
         "\"status\":\"OK\"",
         "\"aal_lpu_handle\":\"fake_lpu\"",
         "\"values\":[\"seq\",\"par\"]",
         "\"min\":1,\"max\":16,\"step\":1",
         "\"min\":2,\"max\":64,\"step\":2",
         "\"description\":\"batch, \\\"quoted\\\"\"",
         "\"scope\":\"PROFILE_QUEUE\"");

  /* valid set, one new version */
  EXPECT("setAalLpuComputeConfig t.mode=par t.workers=8 t.flag=true", "\"status\":\"OK\",\"version\":2");
  EXPECT("getAalLpuComputeConfig", "\"version\":2", "\"t.mode\":\"par\"", "\"t.workers\":8", "\"t.flag\":true");

  /* every error class; none applies anything */
  const int applies = fake_applies;
  EXPECT("setAalLpuComputeConfig t.workers=4 t.mode=fast", "\"status\":\"INVALID_TYPE\"", "\"param\":\"t.mode\"");
  EXPECT("setAalLpuComputeConfig t.workers=4x", "\"status\":\"INVALID_TYPE\"");
  EXPECT("setAalLpuComputeConfig t.flag=maybe", "\"status\":\"INVALID_TYPE\"");
  EXPECT("setAalLpuComputeConfig t.nothing=1", "\"status\":\"UNKNOWN_PARAM\"", "\"param\":\"t.nothing\"");
  EXPECT("setAalLpuComputeConfig t.workers=17", "\"status\":\"OUT_OF_RANGE\"");
  EXPECT("setAalLpuComputeConfig t.batch=3", "\"status\":\"OUT_OF_RANGE\"");
  EXPECT("setAalLpuComputeConfig expected_version=1 t.workers=2", "\"status\":\"VERSION_CONFLICT\"");
  EXPECT("setAalLpuComputeConfig", "\"status\":\"BAD_REQUEST\"");
  EXPECT("setAalLpuComputeConfig expected_version=2", "\"status\":\"BAD_REQUEST\"");
  EXPECT("setAalLpuComputeConfig t.workers=2 t.workers=3", "\"status\":\"BAD_REQUEST\"");
  EXPECT("setAalLpuComputeConfig expected_version=abc t.workers=2", "\"status\":\"BAD_REQUEST\"");
  EXPECT("setAalLpuComputeConfig t.workers", "\"status\":\"BAD_REQUEST\"");
  EXPECT("getAalLpuComputeConfig extra", "\"status\":\"BAD_REQUEST\"");
  EXPECT("noSuchOperation", "\"status\":\"BAD_REQUEST\"");
  CHECK(fake_applies == applies, "a rejected request applied values");
  EXPECT("getAalLpuComputeConfig", "\"version\":2", "\"t.workers\":8", "\"t.mode\":\"par\"");

  /* optimistic concurrency */
  EXPECT("setAalLpuComputeConfig expected_version=2 t.batch=4", "\"status\":\"OK\",\"version\":3");

  /* limits: the effective domain follows the descriptor grid; the value in force is clamped and reported */
  write_file(limits, "t.workers 1 4 # comment\nt.batch 3 9\n");
  snprintf(cmd, sizeof(cmd), "setAalAccelConfig limits=%s", limits);
  EXPECT(cmd, "\"status\":\"OK\"", "\"descriptor_version\":2", "\"version\":4", "\"adjusted\":[\"t.workers\"]");
  EXPECT("getAalLpuComputeCapabilities", "\"min\":1,\"max\":4,\"step\":1", "\"min\":4,\"max\":8,\"step\":2");
  EXPECT("getAalLpuComputeConfig", "\"t.workers\":4", "\"t.batch\":4");
  EXPECT("setAalLpuComputeConfig t.workers=5", "\"status\":\"LIMIT_EXCEEDED\"");
  EXPECT("setAalLpuComputeConfig t.batch=10", "\"status\":\"LIMIT_EXCEEDED\"");

  /* limits that leave no valid value, or are malformed, are rejected and change nothing */
  const char *bad_limits[] = {"t.workers 20 30\n",
                              "t.mode 5 9\n",
                              "t.batch 5 5\n",
                              "t.workers 4 1\n",
                              "t.nothing 1 2\n",
                              "t.workers 1\n",
                              "t.workers 1 99999999999\n"};
  for (size_t k = 0; k < sizeof(bad_limits) / sizeof(bad_limits[0]); k++) {
    write_file(limits, bad_limits[k]);
    EXPECT(cmd, "\"status\":\"BAD_REQUEST\"");
  }
  EXPECT("getAalLpuComputeCapabilities", "\"descriptor_version\":2", "\"min\":1,\"max\":4,\"step\":1");
  EXPECT("setAalAccelConfig limits=/nonexistent/limits.txt", "\"status\":\"BAD_REQUEST\"");

  /* request tokens echoed in the response are escaped */
  EXPECT("foo\"bar", "\"op\":\"foo\\\"bar\"", "\"status\":\"BAD_REQUEST\"");
  EXPECT("setAalLpuComputeConfig t.no\"pe=1", "\"param\":\"t.no\\\"pe\"");

  /* a client that closes without reading must not take the process down (SIGPIPE) */
  {
    const int fd = connect_ctl();
    char burst[64 * 32];
    size_t len = 0;
    for (int k = 0; k < 64; k++)
      len += snprintf(burst + len, sizeof(burst) - len, "getAalLpuComputeCapabilities\n");
    CHECK(write(fd, burst, len) == (ssize_t)len, "write burst");
    close(fd);
    usleep(200000);
    EXPECT("getAalLpuComputeConfig", "\"status\":\"OK\"");
  }

  aal_compute_ext_shutdown();
  CHECK(access(sock_path, F_OK) != 0, "socket file left after shutdown");

  /* a driver that did not register publishes an empty descriptor */
  CHECK(aal_compute_ext_init("other_driver", sock_path, NULL, NULL) == 0, "init without registered LPU");
  EXPECT("getAalLpuComputeCapabilities", "\"aal_lpu_handle\":\"\"", "\"params\":[]");
  EXPECT("setAalLpuComputeConfig t.workers=2", "\"status\":\"UNKNOWN_PARAM\"");
  aal_compute_ext_shutdown();

  /* an initial configuration that violates the limits is refused at startup */
  write_file(limits, "t.workers 1 2\n");
  CHECK(aal_compute_ext_init("fake_lpu", sock_path, limits, "t.workers=3") != 0, "initial config above limit accepted");

  unlink(limits);
  rmdir(dir);
  printf("%s: %d failure(s)\n", failures ? "FAILED" : "PASSED", failures);
  return failures ? EXIT_FAILURE : EXIT_SUCCESS;
}
