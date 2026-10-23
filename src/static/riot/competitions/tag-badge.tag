<tag-badge>
    <span class="comp-tag { opts.size || 'normal' }" style="{ get_category_style() }" title="{ get_category_name() }">
        { get_tag_name() }
    </span>

    <script>
        var self = this

        self.get_tag = function () {
            if (self.opts.tag && typeof self.opts.tag === 'object') {
                return self.opts.tag
            }
            return {
                name: self.opts.name || self.opts.tag || '',
                category: self.opts.category || '',
                category_id: self.opts.category_id || self.opts.categoryId
            }
        }

        self.get_tag_name = function () {
            var tag = self.get_tag()
            return typeof tag === 'string' ? tag : (tag.name || '')
        }

        self.get_category_id = function () {
            var tag = self.get_tag()
            if (tag.category_id != null && !isNaN(tag.category_id)) {
                return Number(tag.category_id)
            }
            if (typeof tag.category === 'number') {
                return tag.category
            }
            if (typeof tag.category === 'string' && !isNaN(tag.category) && tag.category.trim() !== '') {
                return Number(tag.category)
            }
            return null
        }

        self.get_category_name = function () {
            var tag = self.get_tag()
            if (typeof tag.category_name === 'string') {
                return tag.category_name
            }
            if (typeof tag.category === 'string' && isNaN(tag.category)) {
                return tag.category
            }
            return ''
        }

        self.get_category_style = function () {
            var id = self.get_category_id()
            if (!id) {
                var catName = self.get_category_name()
                if (catName) {
                    var hash = 0
                    for (var i = 0; i < catName.length; i++) {
                        hash = catName.charCodeAt(i) + ((hash << 5) - hash)
                    }
                    id = Math.abs(hash)
                }
            }
            if (!id) {
                return 'background-color: hsl(0, 0%, 95%); border: 1px solid hsl(0, 0%, 85%); color: hsl(0, 0%, 40%);'
            }
            var hue = ((id + 45) * 137.5) % 360
            return 'background-color: hsl(' + hue + ', 85%, 90%); border: 1px solid hsl(' + hue + ', 85%, 75%); color: hsl(' + hue + ', 85%, 25%);'
        }
    </script>

</tag-badge>
