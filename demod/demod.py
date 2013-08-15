#!/usr/bin/env python3.3

import demod.config
    
    
def handle_pull(module_or_package_name, pull_request):
    print('handle_pull(module_or_package_name=' + module_or_package_name + ', pull_request)')


config = demod.config.Config()

package_set = config.get_package_set()
module_set = config.get_module_set()

hosted_git = config.create_hosted_git()
repos = module_set.union(package_set)
hosted_git.watch_repositories(repos, handle_pull)


hosted_git.api_call('notifications')




hosted_git.password_mgr.find_user_password(None, 'https://api.github.com/notifications')


base_api = 'https://api.github.com'
api_calls = {
    'notifications': {
        'method':   'GET',
        'url':      base_api + '/notifications',
    },
}
api_urls = [d['url'] for d in api_calls.values()]
