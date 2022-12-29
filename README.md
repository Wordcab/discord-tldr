# Discord TL;DR by Wordcab

Where are on Product Hunt today! [Check it out!](https://www.producthunt.com/posts/discord-tl-dr-by-wordcab)

This repository contains the source code for the Discord bot, Discord TL;DR by Wordcab. It is a bot that summarizes conversations on Discord servers, so you can stay up to date with all your communities, teammates, and friends.

Check out the code to see how it works, and take inspiration from it to build your own Discord bots!

## How to use

* Update the `.env` file with your bot token and the test server ID.

* EC2 auto-deploy: Use the workflow in `.github/workflows/deploy-to-ec2.yml` to deploy your bot to an EC2 instance. You will need to set up the following secrets in your repository:
  - `EC2_HOST`: The hostname of your EC2 instance
  - `EC2_USER`: The username of your EC2 instance
  - `EC2_SSH_KEY`: The private key of your EC2 instance
  - `EC2_TARGET`: The target directory on your EC2 instance

* Docker: We already preapared what it takes to run the bot in a Docker container. All files are in the `docker` directory.

Commands:

```bash
# Build the image
$ docker build --tag discord-bot --file docker/Dockerfile .

# Run the container
$ docker run -d --name discord-bot -v /data:/app/data discord-bot:latest
```
