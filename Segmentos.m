%Trayectoria LSPB (segmentos lineales combinados con segmentos prarabólicos)

%   Parámetros
% tf = tiempo final
% tb  = tiempo de segmento parabólico (tiempo de aceleración)
% q0 = posición inicial
% qf = posición final

%   Condiciones
% Se arranca de la posición inicial en t0, se llega a la posición final en tf.
% v0 y vf deben ser 0
% el perfil llegará a la mitad del movimiento en la mitad del tiempo (q(tf/2)=(q0+qf)/2)
%La velocidad es cte durante el segmento lineal

if (vParam < 0) || (vParam > 1)
 vParam = 0.3;
end

% V1=(qf-q0)/tf;
% V2=2*(qf-q0)/tf;
V=(1+vParam)*(qf-q0)/tf;
tb= (q0-qf+V*tf)/V;

tdiv=2;   %Resolución para cada segundo
t1 = linspace(0,         tb-1/tdiv,       tdiv*tb);
t2 = linspace(tb,        tf-tb-1/tdiv,    tdiv*(tf-2*tb));
t3 = linspace(tf-tb,     tf,              tdiv*tb+1);
t = [t1,t2,t3];
ones1 = ones(size(t1));
ones2 = ones(size(t2));
ones3 = ones(size(t3));
a0 = q0;
a1 = 0;
a2 = V/(2*tb);
b0 = (qf+q0-V*tf)/2;
b1 = V;
c0 = qf-(V*tf^2)/(2*tb);
c1 = (V*tf)/(tb);
c2 = -V/(2*tb);

q1 = a0.*ones1 + a1.*t1 + a2.*t1.^2;
q2 = b0.*ones2 + b1.*t2;
q3 = c0.*ones3 + c1.*t3 + c2.*t3.^2;

v1 = a1.*ones1 + 2*a2.*t1;
v2 = b1.*ones2;
v3 = c1.*ones3 + 2*c2.*t3;

ac1 = 2*a2.*ones1;
ac2 = 0.*ones2;
ac3 = 2*c2.*ones3;

qd=[q1,q2,q3];
vd=[v1,v2,v3];
ad=[ac1,ac2,ac3];
end
