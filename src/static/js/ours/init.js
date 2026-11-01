/*---------------------------------------------------------------------------------
 Runs once on every page, after the HTML has loaded. base.html includes this file.

 It does two things:
 1. Opens and closes the two header menus: the user menu and the mobile menu.
 2. Starts all the Riot tags on the page.

 Why here: the header is on every page, so this code must run on every page.
 */
$(function () {
    /*-----------------------------------------------------------------------------
     Header menus

     The menus are opened with CSS classes:
     - user-menu-open on #user_dropdown shows the user menu (header.styl)
     - mobile-menu-open on the body slides in the mobile menu (mobile_menu.styl)

     aria-expanded tells screen readers if a menu is open or closed.
     */
    // User menu in the header. It only exists when the user is logged in.
    // Why this is safe when logged out: jQuery does nothing on an empty selection.
    const userMenu = $('#user_dropdown')
    const userMenuButton = userMenu.find('.user-menu-button')
    const mobileMenuButton = $('#hamburger_button')

    function setUserMenuOpen(isOpen) {
        userMenu.toggleClass('user-menu-open', isOpen)
        userMenuButton.attr('aria-expanded', isOpen)
    }

    function setMobileMenuOpen(isOpen) {
        $('body').toggleClass('mobile-menu-open', isOpen)
        mobileMenuButton.attr('aria-expanded', isOpen)
    }

    // A click on the username opens the user menu, and a second click closes it
    userMenuButton.on('click', function () {
        setUserMenuOpen(!userMenu.hasClass('user-menu-open'))
    })
    // The mobile menu button only opens the menu, because the open menu covers the button
    mobileMenuButton.on('click', function () {
        setMobileMenuOpen(true)
    })
    // A click on the dark background behind the mobile menu closes it
    $('#mobile_menu_backdrop').on('click', function () {
        setMobileMenuOpen(false)
    })

    // A click outside the user menu closes it
    $(document).on('click', function (event) {
        if (!$(event.target).closest('#user_dropdown').length) {
            setUserMenuOpen(false)
        }
    })

    // The Escape key closes both menus
    $(document).on('keydown', function (event) {
        if (event.key === 'Escape') {
            setUserMenuOpen(false)
            setMobileMenuOpen(false)
        }
    })

    /*-----------------------------------------------------------------------------
     Riotjs

     Finds every Riot tag on the page, like <profile-detail>, and starts it.
     Why last: page scripts must first set the data the tags read, like selected_user.
     */
    riot.mount('*')
})
