# Hyde

This is a static website generator, not unlike many others out there. 
In fact, it probably has a lot fewer features! 

I built this mainly for myself and perhaps it's a good starting point
if you want to build your own static site generator, as there is only very little code and I am making
an effort to document everything well.

## Quickstart

First up, clone this repository. 

`git clone git@github.com:lookingfortrees/hyde.git`

Then, you will need [poetry](https://python-poetry.org/docs/#installation).

Now, to install hyde:
```
$ cd /path/to/repo 
$ poetry install # install all project dependencies
$ poetry shell # activate a shell with hyde loaded
```

You can create a new hyde page and serve it locally like so:

```
$ hyde new ~/mysite # create a new hyde site
$ hyde serve # build and serve the site
```

If you want to change content, take a look at the initial setup in `~/mysite`.

- `content/` contains all your site content, such as blog posts or an about me page.
- `templates/` contains templates to render the HTML pages for the different types of content you have.
- `static/` contains your CSS files or images.
- `output/` is generated when you run `hyde serve` and contains your static website.

















