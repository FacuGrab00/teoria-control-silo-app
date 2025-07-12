$(document).ready(function () {
  const $btnsModo = $('.btn-group-modo button');
  const $contenedorConfig = $('#config-automatico');

  const $switchHumedad = $('#switch-umbral-humedad');
  const $switchTemperatura = $('#switch-umbral-temperatura');
  const $switchVolumen = $('#switch-umbral-volumen');

  const $leyendaHumedad = $('#leyenda-umbral-humedad');
  const $leyendaTemperatura = $('#leyenda-umbral-temperatura');
  const $leyendaVolumen = $('#leyenda-umbral-volumen');

  const $inputTemp = $('#input-temp');
  const $inputHum = $('#input-hum');
  const $inputDist = $('#input-dist');

  const $valorUmbralTemp = $('#valor-umbral-temp');
  const $valorUmbralHum = $('#valor-umbral-hum');
  const $valorUmbralDist = $('#valor-umbral-dist');

  function actualizarEstadoModoVentilador(modo) {
    if (modo === 'manual') {
      $contenedorConfig.addClass('config-automatico-deshabilitado');
    } else {
      $contenedorConfig.removeClass('config-automatico-deshabilitado');
    }
  }

  function enviarModoVentilador(modoStr) {
    const modos = {
      "automatico": 1,
      "manual": 2
    };

    const modo = modos[modoStr];

    if (!modo) {
      alert("Modo inválido");
      return;
    }

    $.ajax({
      url: '/modo_ventilador',
      method: 'POST',
      contentType: 'application/json',
      data: JSON.stringify({ modo }),
      success: function (response) {
        console.log(response.mensaje);
        actualizarEstadoModoVentilador(modoStr);
      },
      error: function (xhr) {
        alert('Error al cambiar modo ventilador: ' + xhr.responseJSON.error);
      }
    });
  }

  function enviarActivacionUmbrales() {
    const dataEnviar = {
      humedad: $switchHumedad.is(':checked'),
      temperatura: $switchTemperatura.is(':checked'),
      volumen: $switchVolumen.is(':checked')
    };

    $.ajax({
      url: '/umbrales',
      method: 'POST',
      contentType: 'application/json',
      data: JSON.stringify(dataEnviar),
      success: function (response) {
        console.log(response.mensaje);
      },
      error: function (xhr) {
        alert('Error al actualizar activación de umbrales: ' + xhr.responseJSON.error);
      }
    });
  }

  function enviarParametros() {
    const temp = Number($inputTemp.val());
    const hum = Number($inputHum.val());
    const dist = Number($inputDist.val());

    const dataEnviar = {
      ...(temp ? { umbral_temperatura: temp } : {}),
      ...(hum ? { umbral_humedad: hum } : {}),
      ...(dist ? { umbral_volumen: dist / 100 } : {}) // convertir cm a m
    };

    if (Object.keys(dataEnviar).length === 0) {
      alert("Ingresá al menos un valor");
      return;
    }

    $.ajax({
      url: '/parametros',
      method: 'POST',
      contentType: 'application/json',
      data: JSON.stringify(dataEnviar),
      success: function (response) {
        alert('Parámetros actualizados correctamente');

        // Actualizar leyendas
        const p = response.valores;
        $valorUmbralTemp.text(p.umbral_temperatura + " °C");
        $valorUmbralHum.text(p.umbral_humedad + " %");
        $valorUmbralDist.text((p.umbral_volumen * 100).toFixed(0) + " cm");

        $leyendaHumedad.text("Umbral actual: " + p.umbral_humedad + " %");
        $leyendaTemperatura.text("Umbral actual: " + p.umbral_temperatura + " °C");
        $leyendaVolumen.text("Umbral actual: " + p.umbral_volumen + " m³");

        // Limpiar inputs
        $inputTemp.val('');
        $inputHum.val('');
        $inputDist.val('');
      },
      error: function (xhr) {
        alert('Error al actualizar parámetros: ' + xhr.responseJSON.error);
      }
    });
  }

  // Estado inicial basado en el botón activo renderizado
  let modoActual = $btnsModo.filter('.active').data('modo');
  actualizarEstadoModoVentilador(modoActual);

  // Eventos
  $btnsModo.click(function () {
    $btnsModo.removeClass('active');
    $(this).addClass('active');
    modoActual = $(this).data('modo');
    enviarModoVentilador(modoActual);
  });

  $switchHumedad.change(enviarActivacionUmbrales);
  $switchTemperatura.change(enviarActivacionUmbrales);
  $switchVolumen.change(enviarActivacionUmbrales);

  $('#enviar-param').click(enviarParametros);
});
