# Open Grind iOS builds

Personal, unofficial build automation for [Open Grind](https://git.opengrind.org/open-grind/open-grind).

Automation lives on `codex/ios-build`; upstream source is mirrored independently to `upstream/ios`. Every six hours, sync checks for changes and builds an unsigned IPA on a standard GitHub-hosted Mac using the official Tauri Action. Manual rebuilds are also supported. Failed builds are retried by later scheduled checks.

Unsigned IPAs need signing with a sideloading tool before installation. This repository does not contain Apple signing credentials and is not an upstream release channel.

Setup is in progress. No successful iPhone build or installation is claimed yet.
