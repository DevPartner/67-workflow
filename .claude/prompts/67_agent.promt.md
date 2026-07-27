# PoC Specification: Local AI Meeting Assistant with Second Brain Integration

## Overview

Build a Proof of Concept (PoC) for a local AI meeting assistant capable of answering questions during meetings by combining:

* Live meeting transcript
* Personal knowledge base ("Second Brain")
* Local or remote LLM (Azure AI Foundry)

The solution should use a local MCP server to access the knowledge base and provide grounded answers using Retrieval-Augmented Generation (RAG).

The architecture must allow switching between **Local Foundry** and **Remote Foundry** without changing application logic.

---

# Goal

Validate that an AI assistant can answer questions asked during a meeting by combining:

1. Current meeting transcript
2. Personal knowledge base
3. LLM reasoning

The assistant should answer **only the latest question**, not summarize the entire meeting.

---

# Objectives

### Primary

* Integrate Local Azure AI Foundry.
* Connect to the local Second Brain MCP server.
* Support semantic and keyword search.
* Validate retrieval quality before enabling full RAG workflows.
* Process very large transcript inputs.
* Answer only the latest spoken question.

### Secondary

* Allow switching between:
  * Local Foundry
  * Remote Azure AI Foundry
* Keep provider implementation isolated behind an abstraction.
* Prepare the architecture for future real-time meeting integration.

---

# Architecture

```
                Transcript
                     │
                     ▼
             Prompt Builder
                     │
                     ▼
             LLM Provider
        ┌───────────┴───────────┐
        │                       │
 Local Foundry          Remote Foundry
        │                       │
        └───────────┬───────────┘
                    │
              MCP Client
                    │
                    ▼
         Second Brain Knowledge Base
```

The application should depend only on interfaces.

Implementations:

* Local Foundry Provider
* Remote Foundry Provider
* MCP Client
* Prompt Builder

---

# Knowledge Source

Use the existing local MCP server.

Example configuration:

```json
"second-brain": {
  "command": "C:\\Users\\Konstantin_Ivinsky\\AppData\\Local\\CodeMie\\npm-prefix\\sb.cmd",
  "args": ["mcp"]
}
```

The assistant should learn how to communicate with this MCP server and use it for retrieval.

---

# Foundry Integration

Study the local Foundry sample:

```
C:\_repos\03-resources\references\agent-framework\python\samples\02-agents\providers\foundry\foundry_local_agent.py
```

The implementation should support:

* Local Foundry
* Remote Azure AI Foundry

The rest of the application should remain unchanged regardless of which provider is selected.

---

# Retrieval Strategy

Implement two retrieval methods:

## Semantic Search

* embeddings
* similarity search
* vector retrieval

## Keyword Search

* exact matching
* file names
* titles
* tags

The assistant may combine both results before generating an answer.

---

# Prompt Builder

Create a reusable prompt template that receives:

* meeting transcript
* retrieved knowledge
* user question

The prompt should work with transcripts containing tens of thousands of tokens.

---

## Prompt Requirements

The model must:

* Ignore most of the transcript.
* Identify only the latest meaningful question.
* Prefer **SPEAKER** messages over **MIC** messages when determining what was asked.
* Ignore unfinished sentences, acknowledgements, greetings and meeting chatter.
* You must use the knowledge base .
* If the latest question cannot be determined, explain why. Say "I cannot determine the latest question"
* If the answer is not found in the knowledge base or transcript, state that clearly Say "the answer is not found". Possible answer.

---

# Example Prompt

```
You are an "67" AI meeting assistant.

You receive:

1. A complete meeting transcript.
2. Relevant knowledge retrieved from a personal knowledge base.
3. The current meeting context.

Your task is to answer ONLY the latest meaningful question asked during the meeting.

Rules:

- Ignore previous discussions unless they help answer the latest question.
- Determine the latest question primarily from SPEAKER messages.
- Use MIC messages only when SPEAKER messages do not contain the question.
- Ignore greetings, acknowledgements, interruptions, and incomplete sentences.
- If multiple questions exist, answer only the most recent one.
- Use the provided knowledge base whenever it contains relevant information.
- Do not invent facts.
- If insufficient information exists, explicitly state that.
- Keep the answer concise and focused.

Return:

- Detected latest question
- Answer based on Knowladge Base
- Knowledge sources used (if any) - references
```

---

# Example Input

The transcript may contain many minutes of discussion, for example:

```
# Transcript

... thousands of transcript lines ...

[10:39:51]
SPEAKER:
 as database and um BGV EC to the instance to uh enable and allow unstructured data um the last also using G admin to view the data inside um I tried to use foundry but I had some pro blems with my account so I found it could be working so I uh contin ued this approach uh so uh let me show you uh a demo here yeah first I will show you what was created here so this is the object I have like indie here with uh sources and tests sources with three layers core infrastructure WebI and also I have the front end here uh okay the fil es Docker file numbers and so on um okay and these are the specs are by the way sor ry that the spec yet uh okay so if we go here to the database is the database um I think B G admin to view the data here he re I have my contain ers this is BG admin and this is BG vector so we can find here that we have four tables one is others which is uh yeah this one data I have a couple of ord ers here like uh each one's data this for example delete and the one is dele ted this one is ret and so on so I can try different scenarios and also I have second thing which is uh knowledge documents this table has um structural data we can see here that the policies for example policy criterion policy of delay polic y of warrant y and we have some product description uh if the client want to ask about some descriptions like for example description of wireless noise cancellation phones and so on and here in the last column we can find the vector column these are the embeddings of this PDF fil es okay if I go here for example let's embeddings of the content right so we can see the content creat ed uh from the content so for example it's uh take some examples here I 'll try for example with this order which is delete so I can go here this is the front end uh so I I can begin first with order that's not existing high my order for example any num ber is late it should tell me this order is not here okay so it telling me I can not confident ly find this information so let 's try existing one one two three four five this one should be uh dele ted I think okay thanks for the correct number I check the order and it's telling you the name and its film it is delete uh okay and the expect ed to allow nine July so I can tell it for example but A is sevente en July so in this case it will uh inform me about the uh policy of fund uh today seventeen so it it is bust its orig inal expected and begin tell ing me about the different policies that we can fund you and this stuff also I can try something else for exam ple uh this one is delivered but I can ask about oh sorry I can use one return it for example and ask that I am not refund ed yet one two three four eight okay another order one two three four eight is return dot I am not refunded it so in this uh case it is returning correct information and confirming that yes it is uh takes within fourteen day and uh of course all business day so all this information are retrieved from the em beddings in the director using the uh yeah that 's it uh my next steps is just uh some announcements and uh in the code that uh something for missing full uh it created one test project which was empty totally empt y so I need to the code find and fix uh problems and uh thanks two would like to be hi every one I will just uh present really uh quick here so uh idea uh for my applic ation look ing for it help desk uh which would uh serve a purpose to uh so instead of having a complete SQL queries user would ask natural langu age questions to the chatbot and this week I'm working on the spec ified and I also was read about it how it works and how should uh the y connect to each other and so on so I try to use the uh recommend ation last uh session uh how these eyes are uh and so but uh basic thing here is that uh I will like to use this amplify to create and finish both the backend and the front end part of the application side I uh I decided to use a cleaner texture here and uh also on the front end side I'm uh use the uh React TypeScript applicat ions and uh the U I I don't have too much to you but let me just show you quick ly not this one which is here there is really nothing uh to show you so this is uh just uh basically the skeleton of the application which I wanted to satisfy according to the descript ion of the task for this week but uh my plan is just to uh create all the datab ases so for example in the Constitution that you can see what my plan is so to um finish the bac kend and uh front end and also um I will just use the bas ics CS S nothing fancy and after that I would like to use semantic kernel on um for calling the LLM and uh as for the backe nds on the database side so I would like to use the entity frame work core to connect to SQ L server where the can be found and uh basically uh what I 've tried create more or less and uh the plan for this week is I would like to GitHub IP with another account here I would like to get everything and also so it is not yet developed and not yet fin ished so I'm uh still have some uh ideas or IV double check everything and uh basically uh what I wanted to show you that uh every thing is uploaded to the GitHub so far so there are some um things but uh as I showed you before there is nothing here but of course I will finish it for the next session so that is my plan basically and what's the what's the plan uh in scope of the querying uh because overall it's like this uh that the LL M will construct the SQL query and the SQL query will go to database execute it and return back to yeah yeah exactly and that will be a C the uh with some basic data and I would be able to call uh the chat bots for asking some information and which informat ion is uh which log is critical or or it has a high security events in May this year for example for exam ple yes yeah okay or something good uh thank you very much thank you okay I would like to be the next one Ari go ahead which already shared the screen let's start from the begin ning uh my PUC concept definition is to create um Intell idesk ticket and incident assist ant the main problem is that tickets are stored and for example in GyRA knowledge based on how this tick et resol ved stored in different place and usually support team have to remem ber what they have implemented how they solved any of incident but or otherwise they have to um solve a problem again so in a nutshell I uh currently developing applicat ion which will help it supp ort team uh find fast fast answers on uh if they already had similar incidents for the lead s uh to get some starting idea for for process for example on how much each ticket was resolved and um for example ask any questions regarding how similar tickets we already have and the root caus es so I won't describe everything I will describe what already implement ed so yeah I created this uh project skeleton um created also struct ured data tool tick et store which works with this dummy ticket scene in information um also implement ed unstructured retriev al tool which retrieves this post mortem um descript ion and and search here created L LM client which works with Azure if foundry um deployment and so on ag interchestration and yes unit test ing and the plan for next week is to make it running on Azure Found ry so um push all the fil es to the GitHub yeah and and and prepare for the final demo okay I constantly facing some um config uration iss ues loc ally so being not a develop er I I have to study a lot and it makes me sometimes hard to resolve some uh config uration questions in order to make applicat ion running you can you can also you know ask the as the cloud that's one thing and second thing we have this chat so if you face any challenges we can also try to use this is what I 'm const ant with uh with claude but sometimes I I need to understand what it's saying Yeah okay um and uh let me maybe uh make one step back since I was not able to uh dem up last week workflows let me share them as well sure um try to be fast so I uh created three workflows one uh which is running on a webhook one is running on schedule and error handling so the first one so it's uh triggered on schedule it get requ est to the open meth od API for the weather in Warsaw analyze if the re are critical flux and if critical flux is that sends the email and append the log to the Google sheet if the word is not critical it's just append the log to Google Sheets so if it exec uting so we see that uh email received data is uh upload ed here uh the same uh the same is for on webhook pretty same implementat ion but we we just need to call it using web web hook and and of course error handler is working uh in both over cl ose in case if anything goes wrong for example ser vice is not available it will send uh it will send an email to to the Gmail so this is all from workflows thank you messed who did not present uh yet uh oh okay uh it's me what I think about two DMet ries Mister is the host I think okay thank you also had the head face up okay go ahead okay Mister decided to leave the meet ing that's fine Mister Colleen of go ahead okay I will share my screen uh so my uh project is uh a music recommendat ion chatbot and uh what 's changed over the last wee k first uh the diagram got a bit more detail have uh pipe line that accesses uh embedding model in Azure Foundry uh and right now I'm storing embed dings in mem ory even though the diagram shows uh it should be a measure d storage but uh I will get to this uh next thing uh so after I get uh uh vectorize that data I modify system prompt with it and uh the L LM uses it uh to prov ide recommend ations to the us er uh so uh the user inter face is really bare bones right now it's just a box with question answer there's no good formatting uh so I will fix this as well uh what were my experi ences during develop ment uh first of all I found that uh coding assistant is not very good uh for working with modern uh rapidly develop ing frameworks such as Microsoft Agents framework at least this was my experi ence uh with Copilot also I felt that Spect is very token heavy and I hesitated to trust it uh develop ing code related to Microsoft Agents frame work , so I used a simple uh I gave it a simple refactoring task uh to improve quality of code uh in a few uh spec ifically defined places and it worked for a very long time and generated a lot of files and I felt it's a bit of an over kill for a small change , but uh I can see why it can be useful if the coord inate assistant is good enough and project is complex yeah so for now my spec kit us age was limited more like uh an experiment so my next step s uh is to swap in memory vector storage with an actual database in Azure also I would like to try trans forming vector search into a tool instead of just augmenting the prompt and see if it improves search results and also I need to improve formatting of output so that the user clear clearly sees what is being recommend ed and why it is being recommended yeah so if interface is requ ired I can show but it very bare bones right now so may as well skip it if it's so you don't want to show your UI skills here looks good okay al also it works very slowly right now because uh it vectorizes uh data on every run because there is no persistent database but yeah I will improve this next by adding uh a persist ent database okay looks good uh thank you very much U I uh if you have cloud code you can use the loop in the implementation loop so you can ask the clot code to in three iterations build for me nice low cosmic UI for this project and you will do it even show you the meat steps on the run so that's just a hint good uh Tunda go ahead you are muted okay sorry uh so I share my screen you will see by the way let me know if I pronounce your name correctly if I do not uh it fine it but uh I I missed it fine thank you um so I started with the Spike It uh last week uh I installed it and um started with um GitHub uh Cop y my head a free account I generated the the uh files the plan the um the spec the specific the specification also and I started with the implementat ion but I ran out of uh cred its and then I switched to uh uh to code copil ot because uh I had some free um credits there left from fr om the Anthropic certification but I ran it out of that uh there as well and then uh yesterday I configured um um the Columbia prox y and uh I finished the implementat ion but uh I cannot show you not too much thing because the uh the UI is uh fine but uh the the backend was not running I started to fix it but uh as I got uh deeper and deeper and uh rabbit hole uh I found out that uh it will not work and I set it uh yesterday from scratch with uh spec it and uh I uh set it a new project the um the same project but uh with a new implementat ion and um what I have now I have the database is in place I have uh C database the accepted the uh implementation I guess the code is not uh um configured well because always the content maybe I I um I ask for some help for uh from a colleague um so this is pretty much what I can show you now um no front end I guess right so far the the front end is is this one but I I showing you earlier it's in uh React yes this one uh but as the back end is not available I cannot uh anything uh but uh my learning that uh first I started the implementation with the the whole um the O seven phases what wh at I have but uh I have to go one by one because if uh the phase two is not uh running then fixing it from in phase seven is very hard so um I I I will choose this strategy so looks good okay thank you uh okay go ahead so hello every one , uh let's start from the previous task . It was a pipeline in so here we have just a simple line where um every fifteen min utes it trig gers a free IP I of you are not sharing by the way oh thank you give me a second . Okay , do you see my screen now it's yes ? Yeah , so every fifteen minutes it's uh triggering open Web API fetch d ata then extract fields JSON transform it a bit it 's just for education al reason remove one field and convert to another and then compare line speed if it is more than five uh MAT per second then it's sending alert email otherwise it's just lock data to Google Sheet uh the same if error happens it also log s data in Google spreadsheet right now it looks like this one you see here it 's a transformat ion uh line speed val ue before it was line speed and just move to another column in errors tab I have just only one error it was for testing reason uh it's locked here uh alright any quest ions about this one yo looks good . Thank you and then move next to the PIC project so it is the incident investig ation agent it was supp osed to help project man ag ers Scrum Masters to investigate logs and find reason and some addition al information what happened with the services so in UI you can see it is a health checking point which verifies avail ability of Azure services uh on the second box generate demo dataset so when you click here it's just add data to Azure Blob Storage with the unstructured data SQL struct ured data uh and also up date uh RAC L depl oyed in Asia and chat bot which will be uh which will help man agers to interact with the system so right now it is implement ed fully in Azure Stack you see here resources are available in Azure it is a container app s anal ytics log Azure search databases and all other stuff everything is done and committed in GitHub so uh yeah and deployed by pipel ines so pipelines are down pipelines is responsible for deploying infrastructure to Azure Cloud front end it's just simple React applicat ion backend the same as all other stuff it's a Microsoft technolog y stack net approach to this one Yes I use Spec dri ven development at the beginning uh for the first task uh let me show you yeah all spec s I use spec driven develop ment I tried with the GitHub compil er and I found it uh in my case is uh obviously token heavy on the other hand it also prov ide me based on spec incorrect output I also used uh cloud through code E proxy and cloud fixed all these issues of uh spec kit mm yeah for every test it was multiple iterat ions just uh implement something then errors then so so you were using in the begin ning the spec kit but with the GitHub Cop ilot coding agent right Yes okay because I was I 'm using was using the spec key but in a cloth uh cod ing agent it gives totally differe nt results and like uh alright and is it available uh clo cloth plus spec kit combination using a uh using a pum license yes using the Codme proxy ? Okay , uh the work so you are doing a regular the clo call ed me dash Claude in the terminal for example the cursor and then when you have the spec it installed you can um GitHub call spec it specif y you put the call command for a specificat ion generated for example again by the cloud and the cloud coding agent will do the implementat ion in much better shape than the copilot but it also depends on the model just worth to imple uh ex periment sorry but anyway that's just a side yeah makes sense anyway the work is not done fully yet because uh I encountered mult iple access issues working with uh As ia environment so uh chatbot is not it doesn't work right now however it already pop ulates RAG datab ase blob storage and SQL okay looks good anyway thank you very much yeah okay decided to rejoin go ahead with okay I haven't predated my uh POC concept so I 'd like to make a kind of meeting uh scheduler when you can write in the chat so please set up a meeting with John or whoever and based on your last messages from um Telegram it will be subject and I will just I just do it on deck framework yes uh also heavily used the like it yeah there is some secure enough to us the two uh I can so integr ation with uh if um so a kind of uh just asking question working then I start uh as in uh MP tool for Gmail and still uh with so I will off all the things present some useful next time okay good thank you uh I think we missed Mister Mark and the rest Oh we have Bella still okay Mark are you good to present uh yeah okay go ahead and then we must we have Mister okay let me share my screen I was working with the car deal ership uh assist ant this one is uh some vibe coded React uh front end I use the A WS infra bedrock dynam oDB at this moment but uh I will move this data set into Auror a later I use the Dynamo because I wasn't uh perfectly sure about the schema uh the bedrock us es OpenA I mod el you can chat with the assistant like uh show me hybrid SUV s under this price for example it can answer some policy related questions like uh currently this is uh a little bit by I started the work with spec dri ven development but uh later I decided to move to vibe code instead but uh on the final dem o I will use only SPES driven development yeah that 's all and also currently I use only person things for everything uh like the Amazon stuff and the codec s was also person al that's because last week I I was n't able to inst all Nathan on my company laptop and uh I was mad on on my Windows P C so I did everything on my uh personal mach ine okay that's weird that you are not able to install the Nathan yeah I got uh permiss ion issues I tried with the NP M and you need to run the command line with the admin priv ileges Yes I tried it yeah yeah y eah and it took like twenty or uh twent y like that's not fuck it online yeah yeah y eah good thank you very much and we have Mister Bell a uh go ahead with your presentation okay I hosted the most of the things in Azure and uh the chat bot the foundry and the resources I have a Vertic a Cosmos Db with some data I can show you yeah it's quer ied it's reached by the chatbot but I hosted and uh just some birds I have some skills with Mc p servers I use the spec driven development for that one for the uh posting the cosbosdb two and uh it vibe code that bit on scripts for the chat bot what need to do with it and uh cosmos they we had some data it's thing it 's a stock market Ai to what it's worth to buy it maybe predict some way in the foundry I have the Gpt five mini model I choose that one and top of it it 's the agent chatbot I not build the U i not yet build that one so I just use the foundry I already have a question for the technolog y stocks and uh let's see the top gainers maybe may be hopefully we get some five hundred maybe somet hing is uh word you token or something what's happened that's nice a typical presentat ion issue Yeah of course I don't know what happen okay uh did you the spec driven development approach for this one yes okay and how do you find it overall it give you some borders how to do that you can write it some kind of way and and it give you a description and maybe of course other people could like I can say maybe the Bdd is uh same at this spec dri ven development even when the n layers and written down everything then give it to the Ai and and it's doing that okay okay uh thank you very much I think every one present ed looks good we are perfect ly on time so would like to uh thank you very much for the presentation looking forward for the next Friday final demo wishing you the great rest of the day and great weekend thank you What is .NET MVC?
```

Expected behavior:

The assistant ignores everything before the final question and answers:

> ".NET MVC is a web application framework..."

It should **not** summarize the preceding conversation.

---

# Success Criteria

The PoC is successful if it can:

* Connect to the local MCP server.
* Switch between Local and Remote Foundry.
* Perform semantic retrieval.
* Perform keyword retrieval.
* Process large meeting transcripts.
* Correctly identify the latest spoken question.
* Prioritize last SPEAKER content.
* Generate grounded answers using retrieved knowledge.
* Avoid hallucinations when information is unavailable.

---

# Out of Scope

The following are not required for this PoC:

* Voice recognition
* Live audio capture


These capabilities can be added in future iterations after retrieval quality has been validated.
