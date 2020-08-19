The scripts included here are used to construct the instructor dashboard where instructors can interactively engage with data from their class.

`app.R` is the main dashboard application script and calls `PLIC_Server.R` and `PLIC_UI.R`, which contain the server and user-interface functions for the app, respectively. `PLIC_DataProcessing.py` includes a function to convert PLIC data, stored in wide form, into long form (on pre/posttest) for use with the dashboard.

`www` contains `.css` files for styling the dashboard.
