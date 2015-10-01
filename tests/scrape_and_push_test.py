# Copyright (c) 2015 ThoughtWorks
#
# See the file LICENSE for copying permission.
import unittest
import openahjo_activity_streams.exceptions as ex
import openahjo_activity_streams.scrape_and_push as sap
import responses


def scraper_returning(results):
    def scrape():
        return results

    return scrape


def failing_scraper():
    raise ex.ScrapeFailureException


def stub_converter(item):
    if item == ConvertFailureItem:
        raise ex.ConvertFailureException
    elif item == StubItem:
        return ConvertedItem
    else:
        return item


class StubPusher:
    def __init__(self):
        self._pushed_items = []

    def push(self, item):
        if item == PushFailureItem:
            raise ex.PushFailureException()
        else:
            self._pushed_items.append(item)

    def pushed_items(self):
        return self._pushed_items


class StubItem:
    pass


class ConvertedItem:
    pass


class ConvertFailureItem:
    pass


class PushFailureItem:
    pass


class ScrapeAndPushTest(unittest.TestCase):
    def setUp(self):
        self.pusher = StubPusher()

    def test__it_orchestrates_scraping_converting_and_pushing_activities(self):
        scraper = scraper_returning([StubItem, StubItem])

        event = sap.scrape_and_push(scrape=scraper, convert=stub_converter, push=self.pusher.push)
        event()

        self.assertEquals(self.pusher.pushed_items(), [ConvertedItem, ConvertedItem])

    def test__it_short_circuits_when_pushing_an_activity_fails(self):
        scraper = scraper_returning([StubItem, PushFailureItem])

        event = sap.scrape_and_push(scrape=scraper, convert=stub_converter, push=self.pusher.push)
        event()

        self.assertEquals(self.pusher.pushed_items(), [ConvertedItem])

    def test__it_short_circuits_when_converting_an_activity_fails(self):
        scraper = scraper_returning([StubItem, ConvertFailureItem])

        event = sap.scrape_and_push(scrape=scraper, convert=stub_converter, push=self.pusher.push)
        event()

        self.assertEquals(self.pusher.pushed_items(), [ConvertedItem])

    def test__it_short_circuits_when_scraping_fails(self):
        scraper = failing_scraper

        event = sap.scrape_and_push(scrape=scraper, convert=stub_converter, push=self.pusher.push)
        event()

        self.assertEquals(self.pusher.pushed_items(), [])


class ScraperTest(unittest.TestCase):
    def test__scrapes_source_endpoint_for_new_data(self):
        coracle_latest_published_time_endpoint = 'http://coracle.endpoint.org/latest_published_activity_timestamp'
        openahjo_endpoint = 'http://openahjo.endpoint.org/agenda_item/'
        query_string = '?last_modified_time__gte=2015-09-01T00%3A00%3A00.000Z&order_by=last_modified_time'

        openahjo_endpoint_with_query_string = openahjo_endpoint + query_string

        with responses.RequestsMock() as rsps:
            rsps.add(responses.GET, coracle_latest_published_time_endpoint,
                     body='{"latest-published-timestamp": "2015-09-01T00:00:00.000Z"}', status=200,
                     content_type="application/json")
            rsps.add(responses.GET, openahjo_endpoint_with_query_string,
                     body="""{"meta":{"limit": 20,
                                      "next": null,
                                      "offset": 0,
                                      "previous": null,
                                      "total_count": 0},
                              "objects": [{"Object": "123"}]}""", status=200,
                     content_type="application/json",
                     match_querystring=True)

            scrape = sap.scraper(coracle_endpoint=coracle_latest_published_time_endpoint,
                                 openahjo_endpoint=openahjo_endpoint)
            agenda_items = scrape()

            self.assertEquals(agenda_items, [{'Object': '123'}])
