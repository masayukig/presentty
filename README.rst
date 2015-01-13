Presentty
=========

Presentty is a console-based presentation program based on
RestructuredText.

Installation
------------

It is recommended, but not required, to install presentty in to a
virtualenv.  To cset one up::

  virtualenv presentty-env
  source presentty-env/bin/activate

To install the latest version from the cheeseshop::

  pip install presentty

To install from a git checkout::

  pip install .

In order to use the cross-fade transition, you must run presentty in a
256-color capable terminal, such as gnome-terminal or xterm.

In order for images to render as ascii art, you must have jp2a
installed.

In order to use figlet and cowsay directives, their respective
programs must be installed.

Usage
-----

Presentty takes the path to the presentation file as an argument.

To run the demonstration included with Presentty, run the following::

  presentty example/demo.rst

Other command line options are available; you can see them with::

  presentty --help

Once presentty is running, you may start an optional presenter's
console in another window with::

  presentty-console example/demo.rst

Once in the presenter's console, you can use the arrow keys and
[enter] to change the current slide, 't' to set the countdown timer
starting value, and [space] to start or stop the timer.

In either the presenter's console or the main presentty window, the
left and right arrow keys or page-up and page-down navigate between
slides.

Source
------

Git repo: https://gitorious.org/presentty

License
-------

Presentty is licensed under the GPLv3 or later.  Please see the
COPYING file for details.
