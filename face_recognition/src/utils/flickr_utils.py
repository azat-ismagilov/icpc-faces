def is_team_photo(tags):
    for tag in tags:
        if tag['raw'] == 'event$Team Photos':
            return True

    return False
