# forgotten

Telegram reminders on demand.

## Configuration

Forgotten expects a configuration file such as the following:

```conf
[tg]
token = TELEGRAM_TOKEN
owner = OWNER_ID

[core]
db_path = /path/to/database/file
wait_time = 15
```

- `token`: can be obtained from the bot father when creating the bot
- `owner`: can be obtained from the bot by executing the `/me` command when it is launched. On the first launch, a value of `0` is recommended before you specify your Telegram ID
- `db_path`: the user must have read/write permissions on the specified path
- `wait_time`: time to wait (in minutes) between each check for reminders that are ready to be sent

## Execution

`FORGOTTEN_CONF=/path/to/conf python3 forgotten.py`

## Commands

- `/adduser <tg_id> <name>`: admin command, adds a user to the database. The ID can be obtained with the `/me` command
- `/listusers`: admin command, list all users in the database
- `/rmuser <tg_id>`: admin command, remove a user from the database, including all their stored reminders
- `/me`: find Telegram ID
- `/remember`: create a new reminder. The bot will ask for both date and message
- `/remember <datetime>`: create a new reminder. The bot will only ask for a message
- `/cancel`: cancel current operation

Note that all dates must be written in `YYYY-MM-DD hh:mm` format.
