# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import types
import re
import random

from configman import Namespace, RequiredConfig

from collector.lib.ver_tools import normalize

Compiled_Regular_Expression_Type = type(re.compile(''))


#--------------------------------------------------------------------------
ACCEPT = 0    # save and process
DEFER = 1     # save but don't process
DISCARD = 2   # tell client to go away and not come back
IGNORE = 3    # ignore this submission entirely


#==============================================================================
class RuleThrottler(RequiredConfig):
    """Throttle incoming crashes based on configured rules

    Throttling lets you vet crashes as they're coming into the system. Maybe you
    want to dump crashes that are clearly junk or statistically sample incoming
    crashes so some subset get processed.

    Throttling rules are applied to the key/value pairs of an incoming crash
    until a matching rule is hit.

    The ``throttle_conditions`` configuration parameter value is a Python list
    of tuples of the form::

        (RawCrashKey?, ConditionFunction?, Probability)

    Specifically:

    * ``RawCrashKey?``: a name of a field from the HTTP POST form. The
      possibilities are: "StartupTime?", "Vendor", "InstallTime?", "timestamp",
      "Add-ons", "BuildID", "SecondsSinceLastCrash?", "UserID", "ProductName?",
      "URL", "Theme", "Version", "CrashTime?" Alternatively, the string "*" has
      special meaning when the ConditionFunction? is a reference to a Python
      function.

    * ``ConditionFunction?``: a function accepting a single string value and
      returning a boolean; regular expression; or a constant used for an
      equality test with the value for the RawCrashKey?. Alternatively, If the
      RawCrashKey? is "*" and the function will be passed the entire raw crash
      as a dict rather than just a single value of one element of the raw
      crash.

    * ``Probability``: an integer between 0 and 100 inclusive. At 100, all JSON
      files, for which the ConditionFunction? returns true, will be saved in
      the database. At 0, no JSON files for which the ConditionFunction?
      returns true will be saved to the database. At 25, there is twenty-five
      percent probability that a matching JSON file will be written to the
      database. Alternatively, the value can be None. In that case, no
      probablity is calculated and the throttler just returns the IGNORE value.
      The crash is not stored and "Unsupported=1" is returned to the client.

    These conditions are applied one at a time to each submitted crash. The
    first match of a condition function to a value stops the iteration through
    the list. The probability of that first matched condition will be applied
    to that crash.

    Example::

        [
            # queue 25% of crashes with version ending in "pre"
            ("Version", lambda x: x[-3:] == "pre", 25),

            # queue 75% of crashes where the inspector addon is at 1.x
            ("Add-ons", re.compile('inspector\@mozilla\.org\:1\..*'), 75),

            # queue all of this user's crashes
            ("UserID", "d6d2b6b0-c9e0-4646-8627-0b1bdd4a92bb", 100),

            # queue all crashes that happened within 5 minutes of another crash
            ("SecondsSinceLastCrash", lambda x: 300 >= int(x) >= 0, 100),

            # ignore Flock 3.0
            ("*", lambda d: d["Product"] == "Flock" and d["Version"] == "3.0", None),

            # queue 10% of what's left
            (None, True, 10)
        ]


    .. Warning::

       You want to avoid bogging down the collector with throttling rules. Put
       most-likely-to-match rules towards the top and keep the list of rules
       small.

    """
    required_config = Namespace()
    required_config.add_option(
      'throttle_conditions',
      doc='the throttling rules',
      default=[
        # drop the browser side of all multi submission hang crashes
        ("*", '''lambda d: "HangID" in d
              and d.get("ProcessType", "browser") == "browser"''', None),
        # 100% of crashes with comments
        ("Comments", '''lambda x: x''', 100),
        # 100% of all aurora, beta, esr channels
        ("ReleaseChannel", '''lambda x: x in ("aurora", "beta", "esr")''', 100),
        # 100% of all crashes that report as being nightly
        ("ReleaseChannel", '''lambda x: x.startswith('nightly')''', 100),
        # 10% of Firefox
        ("ProductName", 'Firefox', 10),
        # 100% of Fennec
        ("ProductName", 'Fennec', 100),
        # 100% of all alpha, beta or special
        ("Version", r'''re.compile(r'\..*?[a-zA-Z]+')''', 100),
        # 100% of Thunderbird & SeaMonkey
        ("ProductName", '''lambda x: x[0] in "TSC"''', 100),
        # reject everything else
        (None, True, 0)
      ],
      from_string_converter=eval
    )
    required_config.add_option(
      'never_discard',
      doc='ignore the Thottleable protocol',
      default=True
    )
    required_config.add_option(
      'minimal_version_for_understanding_refusal',
      doc='ignore the Thottleable protocol',
      default={'Firefox': '3.5.4'},
      from_string_converter=eval
    )

    #--------------------------------------------------------------------------
    def __init__(self, config):
        self.config = config
        self.processed_throttle_conditions = \
          self.preprocess_throttle_conditions(
            config.throttle_conditions
          )

    #--------------------------------------------------------------------------
    @staticmethod
    def regexp_handler_factory(regexp):
        def egexp_handler(x):
            return regexp.search(x)
        return egexp_handler

    #--------------------------------------------------------------------------
    @staticmethod
    def bool_handler_factory(a_bool):
        def bool_handler(dummy):
            return a_bool
        return bool_handler

    #--------------------------------------------------------------------------
    @staticmethod
    def generic_handler_factory(an_object):
        def generic_handler(x):
            return an_object == x
        return generic_handler

    #--------------------------------------------------------------------------
    def preprocess_throttle_conditions(self, original_throttle_conditions):
        new_throttle_conditions = []
        for key, condition_str, percentage in original_throttle_conditions:
            #print "preprocessing %s %s %d" % (key, condition, percentage)
            if isinstance(condition_str, basestring):
                try:
                    condition = eval(condition_str)
                    self.config.logger.info(
                      '%s interprets "%s" as python code' %
                      (self.__class__, condition_str)
                    )
                except Exception:
                    self.config.logger.info(
                      '%s interprets "%s" as a literal for an equality test' %
                      (self.__class__, condition_str)
                    )
                    condition = condition_str
            else:
                condition = condition_str
            if isinstance(condition, Compiled_Regular_Expression_Type):
                #print "reg exp"
                new_condition = self.regexp_handler_factory(condition)
                #print newCondition
            elif isinstance(condition, bool):
                #print "bool"
                new_condition = self.bool_handler_factory(condition)
                #print newCondition
            elif isinstance(condition, types.FunctionType):
                new_condition = condition
            else:
                new_condition = self.generic_handler_factory(condition)
            new_throttle_conditions.append((key, new_condition, percentage))
        return new_throttle_conditions

    #--------------------------------------------------------------------------
    def understands_refusal(self, raw_crash):
        try:
            return normalize(raw_crash['Version']) >= normalize(
                self.config.minimal_version_for_understanding_refusal[
                  raw_crash['ProductName']
                ])
        except KeyError:
            return False

    #--------------------------------------------------------------------------
    def apply_throttle_conditions(self, raw_crash):
        """cycle through the throttle conditions until one matches or we fall
        off the end of the list.
        returns a tuple of the form (
            result:boolean - True: reject; False: accept; None: ignore,
            percentage:float
        )
        """
        #print processed_throttle_conditions
        for key, condition, percentage in self.processed_throttle_conditions:
            throttle_match = False
            try:
                if key == '*':
                    throttle_match = condition(raw_crash)
                else:
                    throttle_match = condition(raw_crash[key])
            except KeyError:
                if key is None:
                    throttle_match = condition(None)
                else:
                    #this key is not present in the jsonData - skip
                    continue
            except IndexError:
                pass
            if throttle_match:  # we've got a condition match - apply percent
                if percentage is None:
                    return None, None
                random_real_percent = random.random() * 100.0
                return random_real_percent > percentage, percentage
        # nothing matched, reject
        return True, 0

    #--------------------------------------------------------------------------
    def throttle(self, raw_crash):
        throttle_result, percentage = self.apply_throttle_conditions(raw_crash)
        if throttle_result is None:
            self.config.logger.debug(
              "ignoring %s %s",
              raw_crash.ProductName,
              raw_crash.Version
            )
            return IGNORE, percentage
        if throttle_result:  # we're rejecting
            #logger.debug('yes, throttle this one')
            if (self.understands_refusal(raw_crash)
                and not self.config.never_discard):
                self.config.logger.debug(
                  "discarding %s %s",
                  raw_crash.ProductName,
                  raw_crash.Version
                )
                return DISCARD, percentage
            else:
                self.config.logger.debug(
                  "deferring %s %s",
                  raw_crash.ProductName,
                  raw_crash.Version
                )
                return DEFER, percentage
        else:  # we're accepting
            self.config.logger.debug(
              "not throttled %s %s",
              raw_crash.ProductName,
              raw_crash.Version
            )
            return ACCEPT, percentage
