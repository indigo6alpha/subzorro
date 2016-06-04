## Introduction

SubZorro is a Reddit bot hosted on Google App Engine, which finds subtitles for Movie or TV Shows content posted on a subreddit.


## How it Works

SubZorro is powered by python and it uses [PTN](https://github.com/divijbindlish/parse-torrent-name) to parse the Movie/TV Show Title and XMLRPCLib to talk to opensubtitles.org's XML-RPC API.


## Python Modules used

- [PTN (parse-torrent-name)](https://github.com/divijbindlish/parse-torrent-name) - to parse the movie/tv titles
- [PRAW](https://praw.readthedocs.io/) - to interact with reddit's API 