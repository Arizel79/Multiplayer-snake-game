// scripts/mobile.js


function isTouchDevice() {
    let is_touch_device = (('ontouchstart' in window) ||
        (navigator.maxTouchPoints > 0) ||
        (navigator.msMaxTouchPoints > 0) ||
        (window.DocumentTouch && document instanceof DocumentTouch) ||
        /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
        (window.innerWidth <= 1024 && window.matchMedia("(any-hover: none)").matches));
        console.log("IsTouchDevice: " + is_touch_device);
        return is_touch_device;
}

function initMobileControls() {
    if (isTouchDevice()) {
        document.getElementById('mobile-controls').style.display = 'block';

        const controlsInfo = document.querySelector('.controls-info');
        if (controlsInfo) {
            controlsInfo.style.display = 'none';
        }

        initMobileControlHandlers();
    }
}


function initMobileControlHandlers() {
    const upBtn = document.getElementById('btn-up');
    const leftBtn = document.getElementById('btn-left');
    const downBtn = document.getElementById('btn-down');
    const centerBtn = document.getElementById('btn-center');
    const rightBtn = document.getElementById('btn-right');
    const fastBtn = document.getElementById('btn-fast');
    const chatBtn = document.getElementById('btn-chat');
    const tabBtn = document.getElementById('btn-tab');

    function sendMoveCommand(direction) {
        if (direction != null) {
            setDirection(direction);
        }
    }

    function addButtonPressedListeners(button) {
        button.addEventListener('touchstart', function(e) {
            e.preventDefault();
            this.classList.add('pressed');
        });

        button.addEventListener('touchend', function(e) {
            e.preventDefault();
            this.classList.remove('pressed');
        });

        button.addEventListener('touchcancel', function(e) {
            e.preventDefault();
            this.classList.remove('pressed');
        });

        button.addEventListener('mousedown', function() {
            this.classList.add('pressed');
        });

        button.addEventListener('mouseup', function() {
            this.classList.remove('pressed');
        });

        button.addEventListener('mouseleave', function() {
            this.classList.remove('pressed');
        });
    }



     let btns = [upBtn, leftBtn, rightBtn, downBtn, centerBtn, tabBtn, chatBtn, fastBtn];
     btns.forEach(btn => {
      addButtonPressedListeners(btn);
    });


    function addButtonListener(btn, func) {
      if (!btn) {
        console.error('Элемент не найден');
        return;
      }

      const handleInteraction = (event) => {
        event.preventDefault();
        func();
      };

      btn.addEventListener('click', handleInteraction);
      btn.addEventListener('touchstart', handleInteraction, { passive: false });
    }
    addButtonListener(chatBtn, () => {
      toggleChat();
    });

    addButtonListener(tabBtn, () => {
      toggleTablist();
    });

    fastBtn.addEventListener('touchstart', function(e) {
        e.preventDefault();
        toggleSpeed(true);
    });

    fastBtn.addEventListener('touchend', function(e) {
        e.preventDefault();
        toggleSpeed(false);
    });

    fastBtn.addEventListener('touchcancel', function(e) {
        e.preventDefault();
        toggleSpeed(false);
    });

    fastBtn.addEventListener('mousedown', function() {
        toggleSpeed(true);
    });

    fastBtn.addEventListener('mouseup', function() {
        toggleSpeed(false);
    });

    fastBtn.addEventListener('mouseleave', function() {
        toggleSpeed(false);
    });

    let activeInterval = null;

    function startMovement(direction) {
        if (activeInterval) {
            clearInterval(activeInterval);
        }

        sendMoveCommand(direction);

        activeInterval = setInterval(() => {
            sendMoveCommand(direction);
        }, 150);
    }

    function stopMovement() {
        if (activeInterval) {
            clearInterval(activeInterval);
            activeInterval = null;
        }
    }

    const movementButtons = [upBtn, leftBtn, downBtn, rightBtn];
    const directions = ['up', 'left', 'down', 'right'];

    movementButtons.forEach((button, index) => {
        const direction = directions[index];

        button.addEventListener('touchstart', function(e) {
            e.preventDefault();
            this.classList.add('pressed');
            startMovement(direction);
        });

        button.addEventListener('touchend', stopMovement);
        button.addEventListener('touchcancel', stopMovement);
        button.addEventListener('mouseleave', stopMovement);
        button.addEventListener('mouseup', stopMovement);
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMobileControls);
} else {
    initMobileControls();
}

window.addEventListener('resize', function() {
    const mobileControls = document.getElementById('mobile-controls');
    if (isTouchDevice()) {
        if (mobileControls.style.display !== 'block') {
            mobileControls.style.display = 'block';
            initMobileControlHandlers();
        }
    } else {
        mobileControls.style.display = 'none';
    }
});