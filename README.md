# pygdo-git

Generic Git watcher for PyGDO. It invokes the local `git` client, so it can
monitor GitHub, GitLab, Gitea, self-hosted repositories, and plain SSH/HTTPS
remotes without a platform API or an access token.

```text
$git.add pygdo https://github.com/gizmore/pygdo.git
$git.abbo pygdo       Subscribe this channel (or your private chat).
$git.abbo pygdo 0     Unsubscribe it again.
$git.log pygdo        Show the local commit history.
```

`git.add` checks a remote out below `files/git_repo/<shortname>/`, remembers
its current head, and does not announce historic commits. The module timer
pulls watched repositories and announces newly received commits to every
subscription. A browser link is derived for common HTTP and SSH forge URLs;
bare Git repositories keep working but naturally have no web commit page.
