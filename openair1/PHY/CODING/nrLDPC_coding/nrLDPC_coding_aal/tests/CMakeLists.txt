# SPDX-License-Identifier: LicenseRef-CSSL-1.0

add_executable(test_aal_compute_ext test_aal_compute_ext.c ../aal_compute_ext.c)
target_include_directories(test_aal_compute_ext PRIVATE ..)
target_link_libraries(test_aal_compute_ext PRIVATE utils minimal_lib pthread)
add_dependencies(tests test_aal_compute_ext)
add_test(NAME test_aal_compute_ext
  COMMAND ./test_aal_compute_ext)
