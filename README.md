<h1 align="center">Discord TL;DR by Wordcab</h1>

<div align="center">
	<a href="https://join.slack.com/t/wordcabcommunity/shared_invite/zt-1n0jo2mxj-47rYqGquR1BeyQwYrkf~kg" target="_blank">
		<img src="https://img.shields.io/badge/JOIN US ON SLACK-4A154B?style=for-the-badge&logo=slack&logoColor=white" />
	</a>
	<a href="https://linkedin.com/company/wordcab" target="_blank">
		<img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" />
	</a>
</div>

<br />
<br />

<div>
	<p>
		See the attached Medium <a href="https://medium.com/@thomaschaigneau.ai/building-and-launching-your-discord-bot-a-step-by-step-guide-f803f7943d33" target="_blank">blog post</a> to read how to use this repository.
	</p>
	<p>
		This repository contains the source code for the Discord bot, Discord TL;DR by Wordcab. It is a bot that summarizes conversations on Discord servers, so you can stay up to date with all your communities, teammates, and friends.
	</p>
	<p>
		Check out the code to see how it works, and take inspiration from it to build your own Discord bots!
	</p>
</div>

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
