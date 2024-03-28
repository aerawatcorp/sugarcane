from flask import render_template


def index_view(ctx):
    # import the master schema
    return render_template("index.html", **ctx)


def browse_view(ctx):
    # import the node schema
    return render_template("browse.html", **ctx)
