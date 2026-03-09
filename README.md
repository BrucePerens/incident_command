# Incident Command Form System

Edit Incident Command forms in a web browser, no PDF involved, and save
the fields as compact JSON that can be sent over packet and reconstituted
into an ICS form. Download or print them as PDF, CSV, JSON. Load JSON
and it populates the form. This is the beginning of automating the ICS
workflow, co-developers wanted. This Python3 program requires Flask,
and should work on any platform that supports Python3.

# Running the Program

Install Flask, download the github repository. Run ics_forms.py, point your
browser to port 5000 on localhost. Email sending is just simulated for now.

# Work Needed!

The field names were picked out of the PDF by a program, and some need tweaking.

This could automate the entire ICS work-flow, with a lot more code. Have at it!
