# Batch URL Expander

## Purpose

This is a simple tool for expanding lots of short URLs in parallel. It is designed to be easy to integrate into longer scripts. 

I have previously used it to clean data extracted from social media sites, listservs, blogs, and chat logs. Expanding short URLs is an endless task, however, so please feel free to make suggestions, corrections, and additions. 

## Usage

The simplest use case looks like this:

    $ python -u expander.py short-urls.txt > short-long-urls.csv
