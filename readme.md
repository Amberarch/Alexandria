## Alexandria

An archiving tool for scribblehub

---

This tool is made for the sole purpose of archiving stories.
All downloads made are for personal use only and are not to be distributed.
All rights to stories belong to the original authors.

This program does work some of the time but scribblehub provides a lot of protections
(which is why this uses selenium rather than curl) so it isn't super consistent.

### Requirements:

* Python 3
* Selenium python package (`python -m pip install selenium`)
* SeleniumWire python package (`python -m pip install seleniumwire`)
* Pypub3 python package (`python -m pip intstall pypub3`)
* Blinker python package (`python -m pip install blinker==1.7.0`)

### Usage:

`python alexandria.py template.html <links to stories>`

As many links as are desired may be entered into any session.
They should be the links as provided in your reading list.
(i.e. in the form `https://scribblehub.com/series/<id>/<name>/`)

Replace template.html with epub for epub export:

`python alexandria.py epub <links to stories>`

### To-Do

* Clean up existing template and provide more adaptive display
* Provide a temporary story buffer to quickly iterate on custom templates
* Provide support for exporting to other formats
