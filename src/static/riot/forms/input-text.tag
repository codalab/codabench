<!-- Field class on initial definition to keep Semantic UI styling -->
<input-text class="field {error: opts.error}">
    <div>
        <label>{ opts.label }</label>
        <input type="text" name="{ opts.name }" ref="input" placeholder="{ opts.placeholder }">
    </div>
    <!--<div class="ui error floating message" show="{ opts.error }">
        <p>{ opts.error }</p>
    </div>-->
    <style>
        /* Make this component "div like" */
        :scope {
            display: block;
        }
    </style>
</input-text>
