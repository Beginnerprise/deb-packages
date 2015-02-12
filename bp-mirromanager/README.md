OS Mirror Manager
===============

Automated OS mirroring and HD failover

## Functionality

These scripts automate the process of:

* Detecting new harddrives added to a machine
* Formatting new drives
* Replicating the primary OS drive
* Making the secondary drive ready for failover
* Keeping the secondary drive synced with the primary drive

## How It Works

These scripts look for new drives added to machine (drives without any partitions).  If detected a prompt will occur at boot (or can be run manually).  If asked confirmed to proceed the secondary drive will be partitioned to match the primary OS drive on the machine.  An appropriate RSYNC will be run, grub installed, and all the various bits necessary to prep the secondary drive for failover.  Additionally a cron job will be added to keep the secondary drive in sync with the first drive.

## Installation

This repo is meant to be built into a deb package for debian.  The installation and this section need some polish
