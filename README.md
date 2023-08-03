# gautodoc

stupid simple autodoc.

## how do I use your stupid tool?

gautodoc operates by looking at the 'roots' of your python project and
recursively searching for imported modules that are part of your project
directory.

if you just want to document a script with some imports, you can just:

```bash
gautodoc init your-script.py
```

this will create .gautodoc in your project folder. `gautodoc init` can also be
used to reconfigure your project if you need it to.

once `.gautodoc` exists, you can run:

```bash
gautodoc build
```

and a `doc/` folder containing a simple static web app will appear!