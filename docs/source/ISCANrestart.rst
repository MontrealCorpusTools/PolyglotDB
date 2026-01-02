.. _restart_iscan:

***************************************
Restarting ISCAN (McGill Team Specific)
***************************************

This section describes instructions for restarting the Roquefort ISCAN server at McGill, in case it is down.

#. Log into the Roquefort server using Michael McAuliffe's username and password.

#. Check if screens exist for pgserver and pgcelery using: ``screen -ls``. If the screens **do not** exist, follow the rest of the instructions exactly. If the screens **do** exist, replace all instances of `screen -S` with `screen -r` in the instructions below.

#. Type the following commands, one line at a time.

    - ``screen -S pgserver``
    - ``source activate pgserver``
    - ``cd /data/mmcauliffe/dev/iscan-spade-server/``
    - ``python manage.py runserver 8080``


#. Press *ctrl+a then d* to close the screen without stopping it. Then type the following  commands.

    - ``screen -S pgcelery``
    - ``source activate pgserver``
    - ``cd /data/mmcauliffe/dev/iscan-spade-server/``
    - ``celery -A iscan_server worker -l info``

#. Press *ctrl+a then d* to close the screen without stopping it. Then, in the main window, run the following command:

    - ``sudo service apache2 restart``

#. The server should now be restarted. Go to **roquefort.linguistics.mcgill.ca** to verify that it is back up.
