# Nicourt Support

Nicourt Support is the remote support client Nicourt uses to help customers
on devices they have authorised. A technician connects only after the person
at the device grants access.

## Origin and licence

This repository is a fork of [RustDesk](https://github.com/rustdesk/rustdesk),
© Purslane Tech Pte. Ltd., and stays under the
[GNU Affero General Public License v3.0](LICENCE). The fork changes the name,
branding and links; the remote desktop engine is RustDesk's. Security fixes
are pulled from upstream regularly.

## What is not in this repository

Server addresses, public keys, signing keys and other secrets are not
committed here. They are supplied at build or deploy time.

## Building

Windows x64 and arm64 builds run in GitHub Actions
(`.github/workflows/flutter-build.yml`). Local builds follow the upstream
RustDesk instructions for the Flutter client.

## Help

- Download and support: <https://support.nicourt.com>
- Issues: <https://github.com/z-xote/nicourt-support/issues>
