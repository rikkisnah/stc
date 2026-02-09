````markdown
# AI System for Ticket Categorization

---

**Adding Rik who will take over from Rob next week.**

Sudha

---

## Confidential – Oracle Internal

**From:** Rahul Chandrakar <rahul.chandrakar@oracle.com>  
**Date:** Tuesday, February 3, 2026 at 7:42 AM  
**To:** Sudha Raghavan <sudha.raghavan@oracle.com>, Tyler Carlton <tyler.carlton@oracle.com>, Rob Colantuoni <rob.colantuoni@oracle.com>  
**Cc:** Ravi Ramanujam <ravi.ramanujam@oracle.com>, Kamalakarthikeyan Venugopal <kamalakarthikeyan.venugopal@oracle.com>  
**Subject:** Re: AI system for ticket categorization  

Hi Sudha,

It is implementable with less friction. We had a chat on the design this afternoon. The team will share the know-how and access with Rob Colantuoni in the Slack channel I have created. Let’s wait for them to sync up and come back with a plan.

Thank you,  
Rahul Chandrakar  
[Architect, OCI Compute]

---

## Confidential – Oracle Internal

**From:** Sudha Raghavan <sudha.raghavan@oracle.com>  
**Date:** Tuesday, February 3, 2026 at 9:09 PM  
**To:** Tyler Carlton <tyler.carlton@oracle.com>  
**Cc:** Rahul Chandrakar <rahul.chandrakar@oracle.com>, Ravi Ramanujam <ravi.ramanujam@oracle.com>, Rob Colantuoni <rob.colantuoni@oracle.com>, Kamalakarthikeyan Venugopal <kamalakarthikeyan.venugopal@oracle.com>  
**Subject:** Re: AI system for ticket categorization  

Any update on the categories for this query from Rahul and the IDC team?

Sudha

---

## Confidential – Oracle Internal

**From:** Tyler Carlton <tyler.carlton@oracle.com>  
**Sent:** Monday, February 2, 2026 at 10:12 PM  
**To:** Sudha Raghavan <sudha.raghavan@oracle.com>  
**Cc:** Rahul Chandrakar <rahul.chandrakar@oracle.com>, Ravi Ramanujam <ravi.ramanujam@oracle.com>, Rob Colantuoni <rob.colantuoni@oracle.com>, Kamalakarthikeyan Venugopal <kamalakarthikeyan.venugopal@oracle.com>  
**Subject:** Re: AI system for ticket categorization  

Ack.

I’d like to start with a sample to ensure it meets your expectations. Once reviewed, we can implement it fully.

Tyler

---

> **On Feb 2, 2026, at 9:20 PM, Sudha Raghavan wrote:**
>
> I want this to be repeatable by me or my TPMs. I know I can get Ravi’s help for one time but I am looking for a system that is self serve. The query was just an example of queries we would like to run.
>
> Sudha

---

## Confidential – Oracle Internal

**From:** Tyler Carlton <tyler.carlton@oracle.com>  
**Sent:** Monday, February 2, 2026 at 9:19 PM  
**To:** Sudha Raghavan <sudha.raghavan@oracle.com>  
**Cc:** Rahul Chandrakar <rahul.chandrakar@oracle.com>, Ravi Ramanujam <ravi.ramanujam@oracle.com>, Rob Colantuoni <rob.colantuoni@oracle.com>, Kamalakarthikeyan Venugopal <kamalakarthikeyan.venugopal@oracle.com>  
**Subject:** Re: AI system for ticket categorization  

Ravi,

Can we rapidly run the results from that query through the system and provide the result for Sudha’s review?

I’m ok with a dev-side hack on C4PO dev to test it out.

Tyler

---

> **On Feb 2, 2026, at 9:09 PM, Sudha Raghavan wrote:**
>
> Adding Kamalakarthikeyan Venugopal.
>
> I would love to see the categorization of issues for tickets in the following query:
>
> ```
> filter=373239 and
> ( labels = GPU_V6_E6-IS_MI355X_S.01 OR "Rack Type" = GPU_MI355X_E6_R.01 )
> and status != "Pending Part(s)"
> ```
>
> Sudha

---

## Confidential – Oracle Internal

**From:** Rahul Chandrakar <rahul.chandrakar@oracle.com>  
**Sent:** Monday, February 2, 2026 at 8:21 PM  
**To:** Ravi Ramanujam <ravi.ramanujam@oracle.com>, Sudha Raghavan <sudha.raghavan@oracle.com>, Rob Colantuoni <rob.colantuoni@oracle.com>, Tyler Carlton <tyler.carlton@oracle.com>  
**Subject:** Re: AI system for ticket categorization  

Thank you, Ravi!  
I will talk to Amit.

Thank you,  
Rahul Chandrakar  
[Architect, OCI Compute]

---

## Confidential – Oracle Internal

**From:** Ravi Ramanujam <ravi.ramanujam@oracle.com>  
**Date:** Tuesday, February 3, 2026 at 9:41 AM  
**To:** Rahul Chandrakar <rahul.chandrakar@oracle.com>, Sudha Raghavan <sudha.raghavan@oracle.com>, Rob Colantuoni <rob.colantuoni@oracle.com>, Tyler Carlton <tyler.carlton@oracle.com>  
**Subject:** Re: AI system for ticket categorization  

Rahul,

We also have an existing issue categorization process which could be a good fit for this:  
https://confluence.oraclecorp.com/confluence/display/OCICOM/Labeling+Automation

If you connect with Amit during your day, he can share more details and how this could be leveraged for CPV.

We use this on a regular basis to identify patterns in issues, raise service improvements, and drive those through DevOps collaboration.

For example, the weekly analysis for the BMP queue for last week.

<image001.png>

---

## Confidential – Oracle Internal

**From:** Rahul Chandrakar <rahul.chandrakar@oracle.com>  
**Date:** Monday, February 2, 2026 at 6:51 PM  
**To:** Sudha Raghavan <sudha.raghavan@oracle.com>, Rob Colantuoni <rob.colantuoni@oracle.com>, Tyler Carlton <tyler.carlton@oracle.com>, Ravi Ramanujam <ravi.ramanujam@oracle.com>  
**Subject:** Re: AI system for ticket categorization  

Hi Sudha, Bob,

C4PO Ops Dashboard is the right platform for automating this. We have a mechanism to download Jira tickets into a delta lake. If the data is structured, we can use Spark to identify pervasive issues. The data can be visible in the C4PO Ops Dashboard. It can handle the throughput ask.

Rob Colantuoni, I will create a channel with the developers of Ops Dashboard. Please share example tickets and any tribal knowledge. I hope your team has bandwidth to make changes.

Thank you,  
Rahul Chandrakar  
[Architect, OCI Compute]

---

## Confidential – Oracle Internal

**From:** Sudha Raghavan <sudha.raghavan@oracle.com>  
**Date:** Tuesday, February 3, 2026 at 8:04 AM  
**To:** Rob Colantuoni <rob.colantuoni@oracle.com>, Tyler Carlton <tyler.carlton@oracle.com>, Ravi Ramanujam <ravi.ramanujam@oracle.com>, Rahul Chandrakar <rahul.chandrakar@oracle.com>  
**Subject:** AI system for ticket categorization  

Hi Tyler, Ravi, Rahul,

I need a way for TPMs and managers in my organization to go to a portal or run a script, etc., to categorize (create Pareto) a set of JIRA tickets. This categorization needs to be done multiple times every day, and we can either give this script a JIRA query or an export of all the tickets. This script should be able to categorize about 100 tickets in 10 minutes (throughput ask).

These tickets are mostly generated by software, so they have the same style of labels and data in them. What we lack is a way to say how many tickets have the “same error,” so we can work on creating scripts to tackle major categories of issues versus closing one ticket at a time. For context, these are not T2 alarm tickets but rather our GPU tests that fail, creating tickets for triage.

Ravi, last time your team did this one-off for around 4,000 tickets for me. I need a repeatable process for much smaller numbers of tickets. I have included Rob, who is my IC5 and can help set this up as well. I need a solution in the next few days. Can you let me know if this is possible?

Sudha
````
