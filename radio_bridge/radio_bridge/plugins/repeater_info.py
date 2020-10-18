from typing import Optional
from typing import Tuple

import re

import structlog
import requests
from bs4 import BeautifulSoup
from expiringdict import ExpiringDict

from radio_bridge.plugins.base import BaseDTMFWithDataPlugin

REPEATERS_URL_2M = "http://rpt.hamradio.si/?modul=repetitorji&vrsta=2"
REPEATERS_URL_70CM = "http://rpt.hamradio.si/?modul=repetitorji&vrsta=3"

# TODO: Support overriding in the config
TEXT = """
Repeater {name}.
Location: {location}.
Input frequency: {input_freq} MHz.
Output frequency: {output_freq}.
CTCSS: {ctcss} MHz
""".strip()

LOG = structlog.getLogger(__name__)

# Dictionary where we stored cached HTTP responses to avoid re-fetching the data when it's not
# necessary. Since those pages rarely change, we use a relatively long TTL.
URL_RESPONSE_CACHE = ExpiringDict(max_len=10, max_age_seconds=(6 * 60 * 60))


class RepeaterInfo(object):
    numeric_id: str
    name: str
    input_freq: str
    output_freq: str
    location: str
    notes: str
    ctcss: Optional[str]

    def __repr__(self):
        return "<RepeaterInfo id=%s,name=%s,input=%s,output=%s,ctcss=%s,location=%s,notes=%s>" % (
            self.numeric_id,
            self.name,
            self.input_freq,
            self.output_freq,
            self.ctcss,
            self.location,
            self.notes,
        )


class RepeaterInfoPlugin(BaseDTMFWithDataPlugin):
    """
    Plugin which retrieves information for a specific VHF / UHF repeater from rpt.hamradio.si and
    displays it.
    """

    ID = "repeater_info"
    NAME = "Repeater info"
    DESCRIPTION = "Display information for a specific repeater."
    # Usage: 38<1 digit for repeater type, 2 = vhf, 7 = 70cm><2 digits for repeater id, e.g. 01>
    # For example 3 8 2 0 1 - First 2m repeater
    # For example 3 8 7 0 1 - First 70cm repeater
    DTMF_SEQUENCE = "38???"

    def run(self, sequence: str):
        repeater_id, repeater_type = self._parse_repeater_id_url_from_sequence(sequence=sequence)

        if repeater_type not in ["vhf", "uhf"]:
            self.say("Invalid repeater type.")
            LOG.info("Invalid repeater type requested with sequence %s" % (sequence))
            return

        LOG.debug('Retrieving information for "%s" repeater "%s"' % (repeater_type, repeater_id))

        repeater_info = self._get_repeater_info(
            repeater_id=repeater_id, repeater_type=repeater_type
        )

        if not repeater_info:
            self.say("Unable to retrieve details for repeater with id %s" % (repeater_id))
            return

        LOG.debug("Retrieved repeater information", repeater_info=repeater_info)

        context = self._get_render_context_for_text(repeater_info=repeater_info)
        text_to_say = TEXT.format(**context)
        self.say(text_to_say)

    def _get_render_context_for_text(self, repeater_info: RepeaterInfo) -> dict:
        """
        Return dictionary which is used as render context when rendering / formatting text to say
        string.
        """
        context = {}
        context.update(repeater_info.__dict__)

        # Format 144.235 -> 1 4 4 [decimal] 2 3 5 so it's more clear when synthesized
        context["input_freq"] = "".join([c + " " for c in context["input_freq"]]).strip()
        context["input_freq"] = context["input_freq"].replace(".", "decimal")
        context["output_freq"] = "".join([c + " " for c in context["output_freq"]]).strip()
        context["output_freq"] = context["output_freq"].replace(".", "decimal")

        if context["ctcss"]:
            context["ctcss"] = "".join([c + " " for c in context["ctcss"]]).strip()
            context["ctcss"] = context["ctcss"].replace(".", "decimal")

        return context

    def _parse_repeater_id_url_from_sequence(self, sequence: str) -> Tuple[str, str]:
        """
        Parse repeater id repeater type (VHF, UHF) from a sequence which is passed to the plugin.
        """
        if len(sequence) != 3:
            # Invalid sequence
            return None, None

        if sequence[0] == "2":
            # 2m repeaters
            repeater_type = "vhf"
        elif sequence[0] == "7":
            # 70cm repeaters
            repeater_type = "uhf"
        else:
            return None, None

        if sequence[1] == "0":
            repeater_id = sequence[2:]
        else:
            repeater_id = sequence[1:]

        return (repeater_id, repeater_type)

    def _get_repeater_info(self, repeater_id: str, repeater_type: str) -> Optional[RepeaterInfo]:
        """
        Retrieve repeater info from the provided URL and for the provided repeater id.
        """
        if repeater_type == "vhf":
            url = REPEATERS_URL_2M
        elif repeater_type == "uhf":
            url = REPEATERS_URL_70CM
        else:
            raise ValueError("Unknown repeater type: %s" % (repeater_type))

        if url not in URL_RESPONSE_CACHE:
            response = requests.get(url)

            if response.status_code != 200:
                LOG.error(
                    "URL %s returned non-200 code" % (url),
                    code=response.status_code,
                    response=response.text,
                )
                return None

            URL_RESPONSE_CACHE[url] = response.text

        response_body = URL_RESPONSE_CACHE[url]
        soup = BeautifulSoup(response_body, "html.parser")

        id_tag = soup.find("b", string=repeater_id)
        if not id_tag:
            return None

        repeater_row = id_tag.find_parent("tr")

        if not repeater_row:
            return

        children = list(repeater_row.children)

        repeater = RepeaterInfo()

        # Some rows contain two frequencies (one for VHF and one for UHF)
        input_freq = re.split(r"\s+", children[3].text)
        output_freq = re.split(r"\s+", children[5].text)

        repeater.input_freq = input_freq[0]
        repeater.output_freq = output_freq[0]

        repeater.numeric_id = children[7].text.strip().split("\n")[0]
        repeater.name = children[7].find("b").text
        repeater.location = children[9].find("b").text

        repeater.notes = children[13].text.strip().replace("\n", " ")

        # Parse CTCSS from the notes (if any if specified)
        match = re.match(r".*CTCSS:\s+((\d+)(\.)(\d+)).*", repeater.notes)

        if match:
            ctcss = match.groups()[0]
        else:
            ctcss = None

        repeater.ctcss = ctcss
        return repeater
