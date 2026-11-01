/*
 * SPDX-License-Identifier: LicenseRef-CSSL-1.0
 */

#ifndef BBDEV_OAI_SW_H
#define BBDEV_OAI_SW_H

#include "aal_compute_ext.h"

/* runtime execution parameters of the baseband_oai_sw LPU (oai_sw.mode, oai_sw.workers, oai_sw.batch) */
const aal_compute_lpu_ops_t *oai_sw_compute_ops(void);

#endif
