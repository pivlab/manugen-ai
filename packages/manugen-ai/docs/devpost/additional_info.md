# Upload a file

I've added the agent architecture diagram.

# Testing Instructions for application

## Intro

First, we encourage you to watch our short video about Manugen-AI [here](https://youtu.be/WkfA-7lXE5w?si=7P_1BMonfFpm_2YE).

To test Manugen-AI, you can either use our hosted demo ([see below](#hosted-demo)) or test it locally from your computer.

## Hosted demo

1. Open the following link in a web browser: https://manugen-ai.cu-dbmi.dev/
1. Click on the lightbulb to load the Markdown example we used in the video.
1. To draft the manuscript, highlight one section at a time (for example, "Introduction", "Results", etc) by selecting the entire section content and click on the "Draft" action, and wait for the text to come back.
1. Drafted sections may be further enhanced by adding instructions to the text, selecting the entire section, and clicking on "Draft".
   The system will edit the existing draft and follow your additional instructions.
1. Figures may be uploaded (it works with PNG format) by clicking on the "Toggle Attachments" button at the top left. If you want to download figures for the example, please see [here](https://github.com/pivlab/manugen-ai/tree/main/frontend/public/example).
1. Once a figure is uploaded, you'll see it gets a figure number like "Figure 1", a title and a description. You can then reference this figure using its figure number (like "Figure 1") in the Results section, and the system will use the Figure title and description.

## Local demo

1. Clone our GitHub repository: https://github.com/pivlab/manugen-ai
1. Follow the instructions in the `README.md`, under section [Installation](https://github.com/pivlab/manugen-ai#installation).
1. Once it's ready, you'll use the URL link to access the frontend locally (such as http://localhost:8901/) and start interacting with the system.

The steps to test the system are the same as described in the "Demo" section above.

# BONUS (Optional)

## A link to your published blog post, video, or podcast

Link to our blog post: https://pivlab.org/2025/06/23/Google-ADK-Hackathon.html

## A link to your contribution to the Agent Development Kit open source repository

https://github.com/pivlab/manugen-ai/issues/11

## List all of the Google Cloud technologies you used in your Project.

Google AI models (`gemini-2.5-flash`), Google AI Studio, Google ADK.
