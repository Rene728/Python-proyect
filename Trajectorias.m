clear
clc
close all
%%Generar la trayectoria
p=0; q=0; pF=5; qF=13; thetaI=0; vRobot=0.1;
d=sqrt( (pF-p)^2 + (qF-q)^2 );
t=d/vRobot

[qd1,vd1,ad1,t] = perfil_lspb(q,qF,140,0.5);
[qd2,vd2,ad2,t] = perfil_lspb(p,pF,140,0.5);

tiledlayout(3,1)
nexttile
plot(t,qd1)
hold on
title("Posición")
xlabel("Tiempo")
ylabel("Posición")
hold off

nexttile
plot(t,vd1)
hold on
title("Velocidad")
xlabel("Tiempo")
ylabel("Velocidad")
hold off

nexttile
plot(t,ad1)
hold on
title("Aceleración")
xlabel("Tiempo")
ylabel("Aceleración")
hold off

function [qd,vd,ad,t] = perfil_lspb(q0,qf,tf,vParam)
