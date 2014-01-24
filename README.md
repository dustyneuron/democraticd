### TODO
Check out https://github.com/agoraciudadana/agora-ciudadana -  django liquid voting, in production use!
Also http://mediagoblin.org/ is sort of similar, and also Django based

### A democratic internet service

- Anyone can propose a change to the live server code
- The users vote on which changes to accept
- No-one has root or shell access - ssh'd is killed, tty's disabled

I call the core service that powers this a *democratic daemon*.

### Future features

- Delegative democracy  
  - You don't have to vote and you still get influence
  - You can say "Auto vote for changes that both Bob & Emily vote for".
- Server forking + per-user data migration  
  - No lock in, anyone can start they're own
  - Niche communities
- Users/donors might pay Bitcoin subscriptions
  - Funding developers
  - System pays it's own hosting costs (autonomous co-operative businesses)
- Modular code
  - So votes can carry forward when unrelated changes get applied
  - You can say "Auto vote for changes to 'webforum' that Dave votes for"

### How it will work

You're browsing the server website, and decide you want to make some changes to the html.
You click the 'fork on github' link, and use GitHub's text editor on GitHub to make the change. When you open your pull request the daemon will automatically put your change up for voting.

To preview your changes you can install the standalone democratic daemon on your pc, which doesn't lock you out but runs the same code. It would be nice if there was way to preview html-only changes on the server - it would have to safely handle/avoid server templating and javascript.

The workflow is similar for system changes like installing & configuring an smpt server - You upload a custom debian source package to GitHub which depends on a mail server, open a pull request and it just works. Alternatively/additionally configuration could be handled by cfengine or similar.

Every registered user can user the server's website to vote for the next change. The status quo option is to say 'I don't want any of these changes', so approved changes might need a quorum of some percentage of the total users.
