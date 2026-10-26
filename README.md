# Open Grind iOS builds

Personal, unofficial build automation for [Open Grind](https://git.opengrind.org/open-grind/open-grind).

Automation lives on `codex/ios-build`; upstream source is mirrored independently to `upstream/ios`. Every six hours, sync checks for changes and builds an unsigned IPA on a standard GitHub-hosted Mac using the official Tauri Action. Manual rebuilds are also supported. Failed builds are retried by later scheduled checks.

Unsigned IPAs need signing with a sideloading tool before installation. This repository does not contain Apple signing credentials and is not an upstream release channel.

## Source and updates

- Browse the application source on [`upstream/ios`](https://github.com/dionoss/open-grind/tree/upstream/ios).
- The sync job preserves upstream commits and refuses rewritten history instead of force-pushing it.
- The macOS build checks out the exact mirrored revision, installs locked dependencies, and uses commit-pinned Actions.
- Preparation converts the prerelease version to Apple's numeric format and replaces the upstream author's team with `0000000000`, a non-account placeholder required by Tauri even with `--no-sign`. These adjustments are included in the artifact.
- No Apple signing credentials are used. These are personal development builds, not upstream signed releases.

## Download an IPA

1. Open [Actions](https://github.com/dionoss/open-grind/actions/workflows/ios.yml) and select a successful run.
2. Download the `open-grind-ios-<upstream-commit>` artifact and extract its ZIP.
3. Check `SHA256SUMS`. On Linux use `sha256sum -c SHA256SUMS`; on macOS use `shasum -a 256 -c SHA256SUMS`.
4. Read `provenance.json` for the source revision, iOS version requirement, and build details.

Artifacts contain the IPA, checksum, provenance, and configuration-adjustment patch. They are retained for 14 days; an expired artifact is rebuilt at the next scheduled check. To rebuild immediately, choose **Run workflow** on the Actions page. Manual runs always build.

## Install on an iPhone

The IPA cannot be installed by merely opening it. Sign and sideload it using a tool such as AltStore Classic, SideStore, or Sideloadly, following that tool's official instructions for your computer and iOS version. A free Apple Account generally requires refreshing the installed app every seven days. A paid Apple Developer membership is not required for this build workflow.

Upstream updates automatically produce new artifacts; they do not automatically update an app already installed on your phone. Sideload a newer IPA to update it.

Validation checks the IPA structure, executable type, arm64 physical-iOS platform, and absence of app signature resources/provisioning profiles. It does not certify an embedded ad-hoc signature or prove iPhone runtime functionality.

## Current verification

Automation tests and workflow validation pass. The first cloud build is being validated; successful iPhone installation and runtime behavior have not been verified.
