// scripts/mobile.js
console.log("init)");
// Функция для определения, является ли устройство тачскринным (без физической клавиатуры)
function isTouchDevice() {
    // Проверяем поддержку тач-событий или наличие тач-устройства
    let is_touch_device = (('ontouchstart' in window) ||
        (navigator.maxTouchPoints > 0) ||
        (navigator.msMaxTouchPoints > 0) ||
        // Для старых браузеров
        (window.DocumentTouch && document instanceof DocumentTouch) ||
        // Определяем мобильные устройства по userAgent
        /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
        // Определяем по размеру экрана и возможности hover
        (window.innerWidth <= 1024 && window.matchMedia("(any-hover: none)").matches));
        console.log("IsTouchDevice: " + is_touch_device);
        return is_touch_device;
}

// Инициализация мобильных контролов
function initMobileControls() {
    // Показываем контролы только на тачскринных устройствах
    if (isTouchDevice()) {
        document.getElementById('mobile-controls').style.display = 'block';

        // Скрываем десктопные подсказки управления
        const controlsInfo = document.querySelector('.controls-info');
        if (controlsInfo) {
            controlsInfo.style.display = 'none';
        }

        // Инициализируем обработчики для мобильных контролов
        initMobileControlHandlers();
    }
}


// Инициализация обработчиков для мобильных контролов
function initMobileControlHandlers() {
    // Получаем элементы кнопок
    const upBtn = document.getElementById('btn-up');
    const leftBtn = document.getElementById('btn-left');
    const downBtn = document.getElementById('btn-down');
    const centerBtn = document.getElementById('btn-center');
    const rightBtn = document.getElementById('btn-right');
    const chatBtn = document.getElementById('btn-chat');
    const tabBtn = document.getElementById('btn-tab');

    // Функция для отправки команд движения
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

    function addButtonListener(button, func) {
        // Для сенсорных устройств
        button.addEventListener('touchstart', func());


        // Для устройств с мышью (тестирование)
        button.addEventListener('mousedown', func());
    }

     let btns = [upBtn, leftBtn, rightBtn, downBtn, centerBtn, tabBtn, chatBtn];
     btns.forEach(btn => {
      addButtonPressedListeners(btn);
    });

//    addButtonListeners(upBtn, 'up');
//    addButtonListeners(leftBtn, 'left');
//    addButtonListeners(downBtn, 'down');
//    addButtonListeners(rightBtn, 'right');

    function addButtonListener(btn, func) {
      // Проверяем, что элемент существует
      if (!btn) {
        console.error('Элемент не найден');
        return;
      }

      // Обработчик кликов и касаний
      const handleInteraction = (event) => {
        // Предотвращаем стандартное поведение для касаний (если нужно)
        event.preventDefault();
        // Вызываем переданную функцию
        func();
      };

      // Добавляем обработчики для мыши и касаний
      btn.addEventListener('click', handleInteraction);
      btn.addEventListener('touchstart', handleInteraction, { passive: false });
    }
    addButtonListener(chatBtn, () => {
      console.log('Кнопка активирована!');
      toggleChat();
    });
    addButtonListener(tabBtn, () => {
      console.log('Кнопка активирована!');
      toggleTablist();
    });
    // Добавляем поддержку удерживания кнопок для непрерывного движения
    let activeInterval = null;

    function startMovement(direction) {
        // Останавливаем предыдущее движение, если есть
        if (activeInterval) {
            clearInterval(activeInterval);
        }

        // Отправляем первую команду сразу
        sendMoveCommand(direction);

        // Затем продолжаем отправлять команды с интервалом
        activeInterval = setInterval(() => {
            sendMoveCommand(direction);
        }, 150); // Интервал в мс (можно настроить)
    }

    function stopMovement() {
        if (activeInterval) {
            clearInterval(activeInterval);
            activeInterval = null;
        }
    }

    // Обновляем обработчики для поддержки удерживания
    const movementButtons = [upBtn, leftBtn, downBtn, rightBtn];
    const directions = ['up', 'left', 'down', 'right'];

    movementButtons.forEach((button, index) => {
        const direction = directions[index];

        // Обновляем обработчики для поддержки удерживания
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

// Запускаем инициализацию при полной загрузке DOM
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMobileControls);
} else {
    initMobileControls();
}

// Также обрабатываем изменение размера окна
window.addEventListener('resize', function() {
    // При изменении размера окна проверяем, нужно ли показывать контролы
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