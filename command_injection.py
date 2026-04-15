# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import ipaddress
import re
import subprocess


def ping_host(hostname: str) -> subprocess.CompletedProcess[str]:
    """Ping a host safely without shell injection.

    Validates the hostname to prevent command injection (CWE-78).
    Only allows valid hostnames and IP addresses.
    """
    _validate_hostname(hostname)
    return subprocess.run(  # noqa: S603
        ["ping", "-c", "1", hostname],  # noqa: S607
        capture_output=True,
        text=True,
        check=False,
    )


def _validate_hostname(hostname: str) -> None:
    """Validate that the hostname is a legitimate hostname or IP address.

    Raises ValueError if the hostname contains characters that could
    be used for command injection or is otherwise invalid.
    """
    if not hostname or not hostname.strip():
        raise ValueError("Hostname must not be empty")

    # Try parsing as an IP address first
    try:
        ipaddress.ip_address(hostname)
        return
    except ValueError:
        pass

    # Validate as a hostname: only alphanumeric, hyphens, and dots allowed
    hostname_pattern = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9\-\.]*[a-zA-Z0-9])?$")
    if not hostname_pattern.match(hostname) or len(hostname) > 253:
        raise ValueError(f"Invalid hostname: {hostname}")
