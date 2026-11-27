/*
 Tags on the benchmark cards (components/benchmark_card.html): one line, at most 4 tags,
 fewer when they do not fit, and "+N more" for the hidden ones.
 Used on the home page and the public competitions page.
 */
(function () {
    // Shows at most this many tags on a card, fewer when they do not fit on one line
    var most_tags_on_card = 4

    // Hides tags from the end until the row fits on one line, and shows "+N more" for the hidden ones.
    // Example: 7 tags on a narrow card -> "Computer Vision  Multimodal  +5 more".
    // Hovering "+N more" lists the hidden tags.
    function fit_tag_row(row) {
        var tags = Array.prototype.slice.call(row.querySelectorAll('.benchmark-card-tag'))
        var more = row.querySelector('.benchmark-card-tag-more')
        var shown = Math.min(tags.length, most_tags_on_card)

        function hide_from(index) {
            tags.forEach(function (tag, i) {
                tag.hidden = i >= index
            })
            // Why only when one is left: a tag that can shrink would hide the overflow,
            // and no tag would move to "+N more"
            tags[0].classList.toggle('benchmark-card-tag-alone', index === 1)

            var hidden_tags = tags.slice(index)
            more.hidden = hidden_tags.length === 0
            more.textContent = '+' + hidden_tags.length + ' more'
            more.title = hidden_tags.map(function (tag) {
                return tag.textContent
            }).join(', ')
        }

        // True when the last visible item ("+N more", or the last tag) ends past the right edge of the row.
        // Why not scrollWidth: it is rounded to whole pixels and can miss a small overflow.
        function overflows() {
            var last = more.hidden ? tags[shown - 1] : more
            return last.getBoundingClientRect().right > row.getBoundingClientRect().right
        }

        // Start with the most allowed, then remove one at a time. The first tag always stays.
        hide_from(shown)
        while (shown > 1 && overflows()) {
            shown -= 1
            hide_from(shown)
        }
    }

    function fit_all_tag_rows() {
        document.querySelectorAll('.benchmark-card-tag-row').forEach(fit_tag_row)
    }

    fit_all_tag_rows()
    // Why: the cards change width when the window does (3, 2 or 1 per row)
    window.addEventListener('resize', fit_all_tag_rows)
    // Why: the fonts load after the first fit and make the row wider,
    // which pushed "+N more" past the edge. Fit again once all fonts are in.
    document.fonts.ready.then(fit_all_tag_rows)
})()
