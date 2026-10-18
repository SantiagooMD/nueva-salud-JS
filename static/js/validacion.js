/*
 * Validación en tiempo real de formularios (SRS 3.1.1).
 *
 * Se activa solo en los formularios que tengan el atributo data-validacion="tiempo-real".
 * Usa las reglas HTML estándar de cada campo (required, min, max, minlength, pattern, step) y
 * muestra el mensaje en rojo debajo del campo apenas el usuario sale de él o lo corrige.
 * Los mensajes en español se leen de atributos data-msg-* del campo:
 *   data-msg-requerido, data-msg-corto, data-msg-min, data-msg-max, data-msg-paso,
 *   data-msg-patron, data-msg-invalido
 * Otros atributos opcionales:
 *   data-max-ahora   -> el máximo del campo de fecha y hora es el momento actual
 *   data-min-campo   -> el mínimo del campo es el valor de otro campo (id), p. ej. "hasta" >= "desde"
 *
 * La validación del servidor sigue siendo la que manda: esto solo da respuesta inmediata.
 */
(function () {
    'use strict';

    var CAMPOS = 'input:not([type=hidden]):not([type=submit]):not([type=button]), select, textarea';

    function mensajeDe(campo) {
        var v = campo.validity;
        var d = campo.dataset;
        if (v.valueMissing || campo.dataset.vacio === '1') return d.msgRequerido || 'Este campo es obligatorio.';
        if (v.tooShort) return d.msgCorto || 'El texto es demasiado corto.';
        if (v.rangeUnderflow) return d.msgMin || 'El valor es menor al mínimo permitido.';
        if (v.rangeOverflow) return d.msgMax || 'El valor es mayor al máximo permitido.';
        if (v.stepMismatch) return d.msgPaso || 'El valor no es válido.';
        if (v.patternMismatch) return d.msgPatron || 'El formato no es válido.';
        if (v.badInput || v.typeMismatch) return d.msgInvalido || 'El valor ingresado no es válido.';
        return campo.validationMessage || 'El valor no es válido.';
    }

    function limpiar(campo) {
        campo.classList.remove('is-invalid');
        var contenedor = campo.parentNode;
        Array.prototype.forEach.call(contenedor.querySelectorAll('.error-campo'), function (e) { e.remove(); });
        if (campo.id) {
            var etiqueta = contenedor.querySelector('label[for="' + campo.id + '"]');
            if (etiqueta) etiqueta.classList.remove('text-danger');
        }
    }

    function mostrar(campo, texto) {
        limpiar(campo);
        campo.classList.add('is-invalid');
        var aviso = document.createElement('div');
        aviso.className = 'error-campo text-danger small mt-1 d-flex align-items-start gap-1';
        aviso.setAttribute('role', 'alert');
        var icono = document.createElement('i');
        icono.className = 'bi bi-exclamation-circle-fill';
        var span = document.createElement('span');
        span.textContent = texto;
        aviso.appendChild(icono);
        aviso.appendChild(span);
        campo.insertAdjacentElement('afterend', aviso);
        if (campo.id) {
            var etiqueta = campo.parentNode.querySelector('label[for="' + campo.id + '"]');
            if (etiqueta) etiqueta.classList.add('text-danger');
        }
    }

    function ahoraLocal() {
        var f = new Date();
        f.setMinutes(f.getMinutes() - f.getTimezoneOffset());
        return f.toISOString().slice(0, 16);
    }

    function prepararLimites(campo, formulario) {
        if (campo.hasAttribute('data-max-ahora')) campo.max = ahoraLocal();
        var origen = campo.getAttribute('data-min-campo');
        if (origen) {
            var otro = formulario.querySelector('#' + origen);
            if (otro && otro.value) campo.min = otro.value; else campo.removeAttribute('min');
        }
    }

    function validar(campo, formulario) {
        if (campo.disabled || campo.type === 'checkbox' || campo.type === 'radio') return true;
        prepararLimites(campo, formulario);
        // Un texto con solo espacios cuenta como vacío en los campos obligatorios.
        var soloEspacios = campo.required && /^(text|search|tel|email|url|textarea)/.test(campo.type)
            && campo.value.length > 0 && campo.value.trim() === '';
        campo.dataset.vacio = soloEspacios ? '1' : '';
        if (campo.validity.valid && !soloEspacios) {
            limpiar(campo);
            return true;
        }
        mostrar(campo, mensajeDe(campo));
        return false;
    }

    function resumen(formulario, invalidos) {
        var previo = formulario.querySelector('.resumen-js');
        if (previo) previo.remove();
        if (!invalidos) return;
        var caja = document.createElement('div');
        caja.className = 'resumen-js alert alert-danger d-flex align-items-start gap-2 rounded-3';
        caja.setAttribute('role', 'alert');
        caja.innerHTML = '<i class="bi bi-exclamation-triangle-fill fs-5"></i><div><strong>Revisa el formulario.</strong> ' +
            'Corrige ' + invalidos + (invalidos === 1 ? ' campo marcado' : ' campos marcados') + ' en rojo antes de continuar.</div>';
        formulario.insertBefore(caja, formulario.firstChild);
    }

    function activar(formulario) {
        var campos = Array.prototype.slice.call(formulario.querySelectorAll(CAMPOS));

        campos.forEach(function (campo) {
            prepararLimites(campo, formulario);
            // Valida al salir del campo y, una vez marcado, mientras el usuario lo corrige.
            campo.addEventListener('blur', function () {
                if (campo.value !== '' || campo.required) validar(campo, formulario);
            });
            var reaccionar = function () {
                if (campo.classList.contains('is-invalid')) validar(campo, formulario);
            };
            campo.addEventListener('input', reaccionar);
            campo.addEventListener('change', function () {
                validar(campo, formulario);
                // Si este campo es el límite de otro (p. ej. "desde"), revalida al dependiente.
                if (campo.id) {
                    Array.prototype.forEach.call(
                        formulario.querySelectorAll('[data-min-campo="' + campo.id + '"]'),
                        function (dep) { if (dep.value) validar(dep, formulario); }
                    );
                }
            });
        });

        formulario.addEventListener('submit', function (evento) {
            var primero = null;
            var invalidos = 0;
            campos.forEach(function (campo) {
                if (!validar(campo, formulario)) {
                    invalidos += 1;
                    if (!primero) primero = campo;
                }
            });
            resumen(formulario, invalidos);
            if (invalidos) {
                evento.preventDefault();
                primero.focus();
                primero.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        Array.prototype.forEach.call(document.querySelectorAll('form[data-validacion="tiempo-real"]'), activar);
    });
})();
