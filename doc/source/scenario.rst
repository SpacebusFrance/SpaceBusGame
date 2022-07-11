.. scenario_

Scenario structure
==================

**Scenarios** are defined by a *xml* file format and should be located in ``data/scenarios`` folder.

The name of the file will be used to identify the scenario in the main menu, so choose it accordingly.

A scenario file is structured as follow

.. code-block:: xml

   <?xml version="1.0" encoding="UTF-8"?>
   <scenario>
      <group name="phase 1">
         <step action="play_sound" name="ok" time_max="0"/>
        ...
      </group>
   </scenario>

.. note:: for the moment, ``group`` commands are ignored and are simply useful for clarity.

A scenario combines two principal elements

- ``step``
- ``event``

Blocking steps
--------------

The first type of action is called a ``step``. They have the particularity to be **blocking**, i.e. the scenario moves
to the next step only if current step is *fulfilled*.

A step can be declared with the ``step`` keyword

.. code-block:: xml

    <step action="play_sound" name="ok" time_max="0"/>

A step is considered *fulfilled* if

1. its **ending conditions** are done

    - in that case, step is ``win``

2. its **life time** is consumed

    - in that case, step is ``lost``

Once the step reaches *one of the previous conditions* (and not both), it is finished and the next step starts.

.. _ec:

Ending conditions
.................

An ending condition corresponds to the value of one or more game's constants. The condition is fulfilled if all desired
constants have the expected values. A condition is defined as

.. code-block:: xml

    <step action="wait">
        <condition key="b_admin" value="True"/>
    </step>

In the previous example, we defined a default ``wait`` step (nothing is done) with one condition : the **button** named
``b_admin`` should be in position ``True``, i.e., should be hit. Once the button will be hit, the step will be fulfilled
and next step will start.

See the :ref:`states` section for the list of available states that can be used as *end conditions*.

You can define several conditions as

.. code-block:: xml

    <step action="wait">
        <condition key="offset_ps_x" value="0.0"/>
        <condition key="offset_ps_y" value="0.0"/>
    </step>

.. important:: the value provided should be written as python code, i.e. ``"True"`` stands for ``True``, ``"0.0"`` for
    ``0.0`` float etc.

Note that you can also provide an interval of values, e.g.

.. code-block:: xml

    <step action="wait">
        <condition key="offset_ps_y" value="[-1.0, 1.0]"/>
    </step>

In that case, the condition is fulfilled if the value lies within this range.

Step life-time
..............

The other possibility to fulfill a step is to define its **life time**. It is provided by the ``time_max`` argument and
should be given in seconds.

.. code-block:: xml

    <step action="wait" time_max="3.1"/>

This code produces a blocking step with no particular action (``action`` set to ``"wait"``) which will block the game
for 3.1 seconds. At the end of this time, next step is played.


.. important:: if a step reaches its **life time**, it is considered as ``lost``. On the other hands, if its
    **end conditions** are fulfilled, it is considered as ``win``.

Step arguments
..............

There is one single mandatory argument for each step, its ``action``.

.. important:: If you set a step as

    .. code-block:: xml

        <step action="wait"/>

    This will generate a **full blocking** step which cannot be ended since it has no life time nor ending conditions.
    Be careful to not block the game !

Below is the list of possible arguments that can be included in **any** step. Note that specific steps may have their
own mandatory arguments (see :ref:`actions`)

- ``action`` : the name of the action to perform (see :ref:`actions` for the list of them)
- ``time_max`` : the life time of this step in seconds
- ``hint_time`` : if specified, defines the time in seconds from the beginning of the step when a ``hint_sound`` should
  be played to help players
- ``hint_sound`` : the name of the sound file to play if ``hint_time`` is provided
- ``id`` : the identifier for the step. If not provided, ``id`` is set to ``step_{n}`` where ``{n}`` is its number (from 0)
- ``loose_sound`` : the sound to play if the task is lost (reach its life-time)
- ``win_sound`` : the sound to play if the task is win (fulfilled its ending conditions)

.. warning:: steps should have a unique ``id`` !

:Example:

    The following code produces a default step with a life time of 20 seconds, playing a hint sound ``hint`` at 10
    seconds and waiting for button ``b_admin``  to be pushed. If the button is pressed, the task status is ``win`` and
    we play a sound ``victory``. No sound is played if the task is lost, i.e. if the button is not pressed before 20
    seconds.

    .. note:: if the step is fulfilled before the hint, the hint sound is not played, obviously

    .. code-block:: xml

        <step action="wait" time_max="20" hint_time="10" hint_sound="hint" win_sound="victory">
            <condition key="b_admin" value="True"/>
        </step>


Punctual events
---------------

The second kind of command is ``event``. It is basically an event that will occur *at a given time* from the start of
current game. It lives *outside* the main ``step`` chain and can be used to represent an event that occurs whatever
current player's step.

.. note:: an ``event`` is punctual and thus has no life time neither ending conditions

An event is created using ``event`` command as

.. code-block:: xml

    <event action="play_sound">

``actions`` and their parameters are described in the :ref:`actions` section.


Event arguments
...............

There are two mandatory argument for each event, its ``action`` and its ``start_time``

Below is the list of possible arguments that can be included in **any** event.

- ``action`` : the name of the action to perform (see XXX for the list of them)
- ``start_time`` : the time between the start of the game and this event in seconds.
- ``id`` : the identifier for the step. If not provided, ``id`` is set to ``event_{n}`` where ``{n}`` is its number (from 0)
