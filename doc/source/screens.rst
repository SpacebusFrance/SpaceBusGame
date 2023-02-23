.. _screens:

Screens
#######

Screens correspond to the look and behavior of the control screen and panel. Each screen has its own set on specific
events that can be triggered.

As for now (2022), there are two different screen named ``lost_astronaut`` and ``go_to_mars`` corresponding to the
two main playable scenarios of the game.

Game screen must be declared at top of the xml scenario file

.. code-block:: xml

    <step action="set_screen" duration="0.0" name="go_to_mars"/>

This command will set the screen corresponding to ``go_to_mars`` scenario.

Go to mars scenario
===================

Below is the list of *go to mars* specific events

start-chrono
------------

Starts the chronometer shown on the screen

*Arguments*

- ``time`` (str): time to wait in seconds

**Note**

You can combine this command with a call to another specific event by adding a ``goto_step`` command with the same
``time``. For example, to jump to the event named *wrong_end* after chronometer ran 60 seconds, we use the following
code

.. code-block:: xml

    <event action="goto_step" goto_id="wrong_end" delay="60"/>
    <step action="start-chrono" time="60" duration="0"/>

start-chrono
------------

Stop the chronometer

reset-chrono
------------

Reset the chronometer (displays 0 seconds)

Lost astronaut scenario
=======================

Below is the list of *lost astronaut* specific events

start-chrono
------------

Starts the chronometer shown on the screen

*Arguments*

- ``time`` (str): time to wait in seconds

start-chrono
------------

Stop the chronometer

reset-chrono
------------

Reset the chronometer (displays 0 seconds)

terminal-show
-------------

Displays the *fake* terminal on the screen

*Arguments*

- ``text`` (str): text to display on the terminal, if there are several lines of text, they will be displayed one
  after each other
- ``focus`` (bool, optional): gives control to the player after text display. Set to ``True`` by default
- ``dt`` (float, optional): time in seconds to wait between each line display. Set to 0.0 by default

terminal-focus
--------------

Sets the focus (keyboard control) on the terminal

*Arguments*

- ``focus`` (bool): gives control to the player after text display
