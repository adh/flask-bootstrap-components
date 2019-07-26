from flask import url_for

def url_or_url_for(url, **kwargs):
    if '/' in url:
        return url.format(**kwargs)
    else:
        return url_for(url, **kwargs)
