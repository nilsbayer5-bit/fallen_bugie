import nmap
import logging

logger = logging.getLogger(__name__)


def run_nmap_scan(target: str) -> dict:
    """Run a nmap top-ports scan (100) and return a structured JSON dict.

    Requires system `nmap` binary and `python-nmap` installed.
    """
    scanner = nmap.PortScanner()
    try:
        # Use -Pn to skip host discovery, --top-ports 100 for top 100 ports and -sV for service/version
        args = "-Pn --top-ports 100 -sV"
        scan_result = scanner.scan(hosts=target, arguments=args)
    except Exception as e:
        logger.exception("nmap scan failed")
        return {"error": str(e)}

    # Parse results into a concise structure
    results = {"hosts": []}
    for host, data in scan_result.get("scan", {}).items():
        host_entry = {"host": host, "status": data.get("status", {}).get("state"), "ports": []}
        proto_ports = data.get("tcp", {})
        for port, portinfo in proto_ports.items():
            host_entry["ports"].append(
                {
                    "port": port,
                    "state": portinfo.get("state"),
                    "name": portinfo.get("name"),
                    "product": portinfo.get("product"),
                    "version": portinfo.get("version"),
                }
            )
        results["hosts"].append(host_entry)

    return results
