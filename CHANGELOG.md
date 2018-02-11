# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## Unreleased

### Added
- Python 3.7 support

### Removed
- Python 3.2 support

### Fixed
- Fix KeyError when using Django memory panel in certain scenarios -- Reported
  by Mark Davidoff (#55), fixed by Pedro Tacla Yamada

## 0.5 - 2017-03-23

### Added
- Add support for Python 3.5 and Python 3.6

### Changed
- Improved runtime performance of summary differ -- By Matt Perpick (#42)
- Include values when sizing named tuples -- Reported by Paul Ellenbogen (#35),
  fixed by Chris Klaiber
- Update bottle.py to 0.12.13

### Removed
- Drop Python 2.5 and Python 3.1 support

## 0.4.3 - 2016-03-31

### Added
- Add Django 1.9 support for DDT panel -- By Benjy (#30)

### Fixed
- Handle untracked classes in tracker statistics -- By gbtami (#33)
- Handle colons in process names gracefully -- By Dariusz Suchojad (#26)
- Support types without `__flags__` attribute in muppy (#24)
- Fix documentation errors (#32, #28, #25) -- By gbtami, Matt, Lawrence Hudson

## 0.4.2 - 2015-07-26

### Fixed
- Include private variables within slots when sizing recursively -- GitHub
  issue #20 report and fix by ddodt
- Fix NameError in memory panel -- GitHub issue #21 reported by relekang

## 0.4.1 - 2015-04-15

### Changed
- Replace Highcharts with Flot (#17)

## 0.4 - 2015-02-03

### Added
- Added memory panel for django-debug-toolbar
- Format tracker statistics without printing -- GitHub issue #2 reported and
  implemented by Andrei Sosnin
- Added close method to ClassTracker
- Support for Python 3.4

### Changed
- Track instance counts of tracked classes without snapshots
- Upgrade to Highcharts 3 and jQuery 1.10

### Removed
- Dropped support for Python 2.4

### Fixed
- Include size of closure variables -- GitHub issue #8 reported and implemented
  by Craig Silverstein
- Fix tkinter import on Python 3 -- GitHub issue #4 reported by pedru-de-huere
- Fix `StreamBrowser.print_tree` when called without arguments -- GitHub issue
  #5 reported by pedru-de-huere
- Fix sizing of named tuples -- GitHub issue #10 reported by ceridwen

## 0.3.1 - 2013-02-16

- Fix class tracker graph data formatting -- Issue 48 reported by Berwyn Hoyt
- Improve web class tracker documentation -- Issue 49 reported by Berwyn Hoyt
- Update links to GitHub and PyPi

## 0.3.0 - 2012-12-29

- Support for Python 3.3

## 0.2.2 - 2012-11-24

- Work around array sizing bug in Python 2.6-3.2 -- Issue 46 reported by Matt
- Fix import when python is run with optimization `-OO` -- Issue 47 reported by
  Kunal Parmar

## 0.2.1 - 2011-11-13

- Fix static file retrieval when installed via easy_install
- Show class tracker instantiation traces and referent trees in web interface
- New style for web interface

## 0.2

The second release is one of several steps to better integrate the different
sub-systems of Pympler. All modules now directly reside in the pympler namespace
which simplifies the import of Pympler modules.  Pympler 0.2 introduces a web
interface to facilitate memory profiling.  Pympler now fully supports Python
3.x. This release also adds several modules replacing the *Heapmonitor* module
with the new *class tracker* facility.

- Introduce web frontend
- Split Heapmonitor into several new modules
- New `process` module to obtain memory statistics of the Python process
- Improved garbage illustration which can directly render directed graphs using
  graphviz

## 0.1

This initial release is the first step to unify three separate Python memory
profiling tools. We aim to create a place-to-go for Python developers who want
to monitor and analyze the memory usage of their applications. It is just the
first step towards a further integration. There is still lots of work that
needs to be done and we stress that the API is subject to change. Any feedback
you want to give us, wishes, bug reports, or feature requests please send them
to **pympler-dev@googlegroups.com**.
