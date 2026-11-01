/*
 * SPDX-License-Identifier: LicenseRef-CSSL-1.0
 */

/*
 * AAL compute extension: runtime execution parameters of an AAL-LPU.
 *
 * The LPU describes the parameters it accepts while its queues keep running (a typed descriptor), the AAL
 * Implementation intersects that descriptor with the limits set by the infrastructure (IMS -> HAM) and validates
 * requests generically, by type and range, without knowing what a parameter means. An LPU driver that does not
 * implement aal_compute_lpu_ops_t publishes an empty descriptor, so applications that ignore the extension keep
 * working unchanged.
 */

#ifndef AAL_COMPUTE_EXT_H
#define AAL_COMPUTE_EXT_H

#include <stdint.h>

#define AAL_COMPUTE_MAX_PARAMS 16
#define AAL_COMPUTE_MAX_ENUM_VALUES 8
/* configuration versions kept in the per-version statistics */
#define AAL_COMPUTE_STATS_VERSIONS 64

typedef enum {
  AAL_COMPUTE_TYPE_INT,
  AAL_COMPUTE_TYPE_ENUM,
  AAL_COMPUTE_TYPE_BOOL,
} aal_compute_type_t;

typedef enum {
  AAL_COMPUTE_CATEGORY_PARALLELISM,
  AAL_COMPUTE_CATEGORY_BATCHING,
  AAL_COMPUTE_CATEGORY_MEMORY,
  AAL_COMPUTE_CATEGORY_OTHER,
} aal_compute_category_t;

/* the three configurable objects of the AAL Common API (AAL-LPU, profile instance, profile queue) */
typedef enum {
  AAL_COMPUTE_SCOPE_LPU,
  AAL_COMPUTE_SCOPE_PROFILE_INSTANCE,
  AAL_COMPUTE_SCOPE_PROFILE_QUEUE,
} aal_compute_scope_t;

/* One entry of the descriptor. ENUM values are carried as the index into enum_values; BOOL as 0 or 1. */
typedef struct {
  const char *name;
  aal_compute_type_t type;
  int32_t min;
  int32_t max;
  int32_t step;
  int nb_enum_values;
  const char *enum_values[AAL_COMPUTE_MAX_ENUM_VALUES];
  int32_t default_value;
  const char *unit;
  aal_compute_category_t category;
  aal_compute_scope_t scope;
  const char *description;
} aal_compute_param_t;

typedef struct {
  uint32_t version;
  uint64_t t_applied_ns; /* CLOCK_MONOTONIC: the LPU finished applying this version */
  uint64_t t_first_burst_ns; /* CLOCK_MONOTONIC: first burst processed with this version, 0 if none yet */
  uint64_t nb_bursts;
  uint64_t nb_ops;
  uint64_t busy_ns; /* time spent processing bursts of this version */
} aal_compute_stats_t;

/*
 * Implemented by an LPU driver. Values are indexed as the descriptor; the AAL Implementation only calls apply()
 * with a complete, already validated vector. A new configuration takes effect at the next burst: a burst in progress
 * finishes with the configuration it started with.
 */
typedef struct {
  const char *lpu_handle;
  int nb_params;
  const aal_compute_param_t *params;
  /* applies all values at once and returns the new configuration version */
  uint32_t (*apply)(const int32_t *values);
  /* copies the values in force and returns their version */
  uint32_t (*get)(int32_t *values, uint64_t *t_applied_ns);
  /* fills up to max entries, most recent version first, and returns how many were filled */
  int (*get_stats)(aal_compute_stats_t *stats, int max);
} aal_compute_lpu_ops_t;

/*
 * Starts the extension for the bbdev driven by driver_name: applies the infrastructure limits (limits_file, may be
 * NULL), then the initial configuration (initial_config, "name=value,name=value", may be NULL), and serves the
 * AALI-C-App operations on the UNIX socket ctl_sock.
 */
int aal_compute_ext_init(const char *driver_name, const char *ctl_sock, const char *limits_file, const char *initial_config);
void aal_compute_ext_shutdown(void);

#endif
