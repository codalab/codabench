import datetime
from unittest import mock

from django.test import TestCase
from django.urls import reverse

from factories import PaperFactory


class HallOfPapersViewTests(TestCase):
    def setUp(self):
        self.p1 = PaperFactory(
            title='Alpha Vision Benchmark',
            authors='Alice Smith',
            venue='CVPR',
            publication_date=datetime.date(2024, 6, 1),
            citation_count=30,
        )
        self.p2 = PaperFactory(
            title='Beta NLP Challenge',
            authors='Bob Martin, Carol White, Dan Brown',
            venue='ACL',
            publication_date=datetime.date(2025, 2, 1),
            citation_count=5,
        )
        self.p3 = PaperFactory(
            title='Gamma Robotics Suite',
            authors='Carol White',
            venue='ICRA',
            publication_date=datetime.date(2025, 5, 1),
            citation_count=15,
        )
        self.p4 = PaperFactory(
            title='Delta Climate Model',
            authors='Dan Brown',
            venue='NeurIPS',
            publication_date=datetime.date(2023, 12, 1),
            citation_count=50,
        )
        self.hidden = PaperFactory(
            title='Hidden Draft Paper',
            publication_date=datetime.date(2026, 1, 1),
            is_visible=False,
        )

    def test_list_page_default_order_and_visibility(self):
        resp = self.client.get(reverse('papers:list'))
        self.assertEqual(resp.status_code, 200)
        titles = [p.title for p in resp.context['papers']]
        self.assertEqual(titles, [
            'Gamma Robotics Suite',
            'Beta NLP Challenge',
            'Alpha Vision Benchmark',
            'Delta Climate Model',
        ])

    def test_search_and_filters(self):
        resp = self.client.get(reverse('papers:list'), {'search': 'NLP'})
        self.assertEqual([p.id for p in resp.context['papers']], [self.p2.id])

        resp = self.client.get(reverse('papers:list'), {'min_citations': '20', 'ordering': 'citations'})
        self.assertEqual([p.id for p in resp.context['papers']], [self.p4.id, self.p1.id])

        resp = self.client.get(reverse('papers:list'), {'start_date': '2025-01-01'})
        self.assertEqual({p.id for p in resp.context['papers']}, {self.p2.id, self.p3.id})

    def test_home_page_shows_3_latest_visible_papers(self):
        resp = self.client.get(reverse('pages:home'))
        self.assertEqual(resp.status_code, 200)
        latest = list(resp.context['latest_papers'])
        self.assertEqual(len(latest), 3)
        self.assertEqual([p.id for p in latest], [self.p3.id, self.p2.id, self.p1.id])

    def test_authors_summary(self):
        self.assertEqual(self.p1.authors_summary, 'Alice Smith')
        self.assertEqual(self.p2.authors_summary, 'Bob Martin, Carol White +1 author')
        many = PaperFactory(authors='A, B, C, D, E')
        self.assertEqual(many.authors_summary, 'A, B +3 authors')

    def test_deleting_paper_removes_thumbnail_from_storage(self):
        paper = PaperFactory(thumbnail='paper_thumbnails/test.webp')
        with mock.patch.object(paper.thumbnail.storage, 'delete') as mock_delete:
            with self.captureOnCommitCallbacks(execute=True):
                paper.delete()
        mock_delete.assert_called_once_with('paper_thumbnails/test.webp')
