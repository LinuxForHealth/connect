# Connect on arm64
The steps to run connect on arm64 are the same as described in the main [README](../../README.md), except when working with certificates.

## Working with certificates
Perform this step if you want to create new certificates for connect and connect services. The creation of new certificates is not required, as connect contains a set of default certificates for SSL.

### Install mkcert
Uninstalling existing certificates and creating new certificates requires the mkcert utility, which has been built for you on arm64. To use mkcert, you must place it on your path.  You can leave mkcert in place and add connect/platforms/arm64 to your path, or you can copy connect/platforms/arm64/mkcert to another directory already on your path.

For all other instructions, please refer to the top-level [README](../../README.md) or the [LinuxForHealth documentation](https://linuxforhealth.github.io/docs/).