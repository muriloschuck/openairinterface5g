#!/usr/bin/env python3
"""stub_aal.py: control client for the AAL compute extension (stands for the xApp/control client of the TCC).

    tools/tcc/stub_aal.py caps
    tools/tcc/stub_aal.py get
    tools/tcc/stub_aal.py set oai_sw.mode=par oai_sw.workers=4 [expected_version=N]
    tools/tcc/stub_aal.py stats
    tools/tcc/stub_aal.py limits /tmp/aal_ext_limits.txt

Sends one request line to the UNIX socket opened by nr_ulsim (--nrLDPC_coding_aal.ctl_sock, default
/tmp/aal_ext.sock) and prints the JSON response. For set, t0_ns (CLOCK_MONOTONIC, taken just before sending) is
added to the output, so that t1 - t0 can be computed against t_applied_ns. Exit code 0 if status is OK.
"""
import argparse
import json
import socket
import sys
import time

OPS = {
    "caps": "getAalLpuComputeCapabilities",
    "get": "getAalLpuComputeConfig",
    "set": "setAalLpuComputeConfig",
    "stats": "getAalLpuComputeStats",
    "limits": "setAalAccelConfig",
}


def request(sock_path, line):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.connect(sock_path)
        t0 = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
        s.sendall((line + "\n").encode())
        buf = b""
        while not buf.endswith(b"\n"):
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
    return t0, json.loads(buf)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sock", default="/tmp/aal_ext.sock")
    ap.add_argument("op", choices=OPS)
    ap.add_argument("args", nargs="*")
    a = ap.parse_args()
    args = a.args
    if a.op == "limits":
        if len(args) != 1:
            ap.error("limits takes one file")
        args = [f"limits={args[0]}"]
    t0, resp = request(a.sock, " ".join([OPS[a.op]] + args))
    if a.op == "set":
        resp["t0_ns"] = t0
    print(json.dumps(resp, indent=2))
    return 0 if resp.get("status") == "OK" else 1


if __name__ == "__main__":
    sys.exit(main())
