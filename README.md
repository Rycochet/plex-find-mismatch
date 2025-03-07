# plex-find-mismatch

[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/Rycochet/plex-find-mismatch/publish.yml)](https://github.com/Rycochet/plex-find-mismatch/actions/workflows/publish.yml) ![GitHub contributors](https://img.shields.io/github/contributors/Rycochet/plex-find-mismatch) [![Docker Pulls](https://img.shields.io/docker/pulls/rycochet/plex-find-mismatch) ![Docker Image Size](https://img.shields.io/docker/image-size/rycochet/plex-find-mismatch)](https://hub.docker.com/r/rycochet/plex-find-mismatch/)

Finds incorrectly matched media folders in Plex. This requires you to include the [TVDB](https://thetvdb.com/), [TMDB](https://www.themoviedb.org/), or [IMDB](https://www.imdb.com/) id in the folder path as per the Plex (and TRaSH guide) recommendations.

Specifically include `{tvdb-<TVDB id>}` / `{tvdb-<TMDB id>}` / `{imdb-<IMDB id>}` in the folder path for the TV Show or Movie, and this script will tell you when Plex is matching against the wrong source.

> [!NOTE]
> While the IMDB is a single consistent id, the others get more data from the general public and as such you may have some media matched against a removed ID - generally the more recently an entry is made to them the more likely two (or more) have been added, and the duplicates will be removed. This only checks if Plex matches the folder name, but Plex itself will remove a link if that gets removed!

## Running

### Python

This is a standard Python script, and should be run however you would normally run anything with Python. It requires [python-plexapi](https://github.com/pkkid/python-plexapi), [python_dotenv](https://github.com/theskumar/python-dotenv), and [schedule](https://github.com/dbader/schedule) installed and available.

### Docker

This is designed to be used via Docker / Docker Compose, all options are available via environmental variables, with sensible defaults.

```yaml
services:
  plex-find-mismatch:
    image: rycochet/plex-find-mismatch:latest
    network_mode: host # Ensure this has access to plex
    environment:
      PLEX_TOKEN: "YOURTOKENVALUEHERE"
    volumes:
      # Copy the same media paths you supply to Plex
```

## Environment Variables

| Name | Definition | Default |
| --- | --- | --- |
| `PLEX_TOKEN` **or** <br> `PLEX_TOKEN_FILE` [^1] | **Required** <br> A Plex authentication token (see [the Plex docs](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/)) | |
| `PLEX_URL` | The URL to access Plex on. | `http://localhost:32400` |
| `LOG_LEVEL` | How much to log. All mismatches are WARNING, so all other information can be hidden easily hidden. Must be one of `DEBUG`, `INFO`, `WARNING`, or `ERROR`. | `DEBUG` |
| `CHECK_ADD_LABEL` | Should a label be added to the item within Plex. This makes it easy to add a filter for the specific `FixMatch` label. | `true` |
| `CHECK_UNMATCH` | This will force Plex to unmatch, but can't help Plex to find the correct match. It is useful to stop Plex from serving up incorrect information, but still need manual correction. | `true` |
| `CHECK_NOW` | If set then this will run once and then quit. | `true` if running in a shell |
| `CHECK_AT` | Time(s) to check every day. By default this checks half an hour after Plex does it's daily udates, but you can supply a list of comma separate times for multiple checks. | `06:30` |
| `CHECK_AGENTS` | A comma separated list of agents to check against. | `tvdb,tmdb,imdb` |
| `CHECK_LIBRARY` | A comma separated list of (case insensitive) Plex library names to check. By default it will look at all libraries by using a `*` wildcard, but this can optimise performance slightly. | `*` |
| `CHECK_PATH<n>` **and** `CHECK_PATH<n>_REPLACE` | Paired paths for replacing from the Plex config. This is most useful when running in a shell and the path mappings are different. Note that you may only include nine (9) at most. | |
