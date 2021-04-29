#
# (C) Copyright IBM Corp. 2020
#
# SPDX-License-Identifier: Apache-2.0
#
# make-certs.sh
# Creates the LinuxForHealth certificates required to enable TLS.
#
rm *.pem *.p12 *.crt *.csr *.key *.old *.pem index.txt* serial.txt* > /dev/null 2>&1
touch index.txt
echo "01" > serial.txt
