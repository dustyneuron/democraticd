## An enforced democratic server

- Anyone can propose a change to the live server code
- The users vote on which changes to accept
- No-one has root or shell access - ssh'd is killed, tty's disabled

I call the core service that powers this a *democratic daemon*.

### Features
- Delegative democracy so non-devs can use it, + you can say "Auto vote for changes that both Bob & Emily vote for".
- Server forking + per-user data migration, for contentious issues and creating niche communities.
- Users might pay subscriptions, and vote for funding devs & paying server costs.
- Modular code so votes can carry forward between changes + you can say "Auto vote for changes to 'webforum' that Dave votes for"

